"""
MessagePack RPC bridge for Universal Library Loader.

This bridge enables cross-language communication using a length-prefixed
MessagePack binary protocol over stdin/stdout.
"""

# ADC-IMPLEMENTS: <rpc-feature-01>

import struct
import subprocess
from pathlib import Path
from typing import Any, List, Optional

try:
    import msgpack
except ImportError:
    raise ImportError(
        "msgpack library required for RPC bridge\n"
        "  Install: pip install msgpack\n"
        "  Or: uv pip install msgpack"
    )

from ..exceptions import LibraryLoadError


class RPCError(Exception):
    """Exception raised when remote RPC method fails."""
    pass


class RPCTimeoutError(RPCError):
    """Exception raised when RPC call times out."""
    pass


class RPCBridge:
    """MessagePack RPC bridge for cross-language communication."""

    def __init__(
        self,
        command: List[str],
        timeout: float = 30.0,
        workspace_path: Optional[Path] = None
    ):
        """
        Launch subprocess RPC server with stdio communication.

        Args:
            command: Command to start RPC server (e.g., ["dart", "run", "bin/serve.dart"])
            timeout: Default timeout for RPC calls in seconds
            workspace_path: Working directory for subprocess (optional)

        Raises:
            LibraryLoadError: If subprocess fails to start
        """
        self.command = command
        self.timeout = timeout
        self.workspace_path = workspace_path
        self.process: Optional[subprocess.Popen] = None

        # Launch subprocess
        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(workspace_path) if workspace_path else None,
            )
        except FileNotFoundError as e:
            raise LibraryLoadError(
                f"Failed to start RPC server: command not found\n"
                f"  Command: {' '.join(command)}\n"
                f"  Error: {e}\n"
                f"  Fix: Ensure runtime is installed (dart, node, etc.)"
            )
        except Exception as e:
            raise LibraryLoadError(
                f"Failed to start RPC server\n"
                f"  Command: {' '.join(command)}\n"
                f"  Error: {e}"
            )

        # Verify process started successfully
        if self.process.poll() is not None:
            # Process already exited
            stderr_output = self.process.stderr.read().decode('utf-8', errors='replace')
            raise LibraryLoadError(
                f"RPC server exited immediately after launch\n"
                f"  Command: {' '.join(command)}\n"
                f"  Exit code: {self.process.returncode}\n"
                f"  Stderr: {stderr_output}"
            )

    def call(self, method: str, **kwargs) -> Any:
        """
        Send RPC request and wait for response.

        Args:
            method: Method name to call on remote server
            **kwargs: Method arguments as keyword parameters

        Returns:
            Deserialized result from remote method

        Raises:
            RPCError: If remote method raises exception
            RPCTimeoutError: If response not received within timeout
            LibraryLoadError: If subprocess has died
        """
        if self.process is None:
            raise LibraryLoadError("RPC bridge not initialized - call __init__ first")

        if self.process.poll() is not None:
            # Process has died
            stderr_output = self.process.stderr.read().decode('utf-8', errors='replace')
            raise LibraryLoadError(
                f"RPC server process has died\n"
                f"  Command: {' '.join(self.command)}\n"
                f"  Exit code: {self.process.returncode}\n"
                f"  Stderr: {stderr_output}"
            )

        # Build request
        request = msgpack.packb({"c": method, "a": kwargs})
        length_header = struct.pack('>I', len(request))

        # Send request
        try:
            self.process.stdin.write(length_header)
            self.process.stdin.write(request)
            self.process.stdin.flush()
        except BrokenPipeError:
            stderr_output = self.process.stderr.read().decode('utf-8', errors='replace')
            raise LibraryLoadError(
                f"RPC server closed connection\n"
                f"  Command: {' '.join(self.command)}\n"
                f"  Stderr: {stderr_output}"
            )

        # Read response length header (4 bytes)
        try:
            length_bytes = self.process.stdout.read(4)
            if len(length_bytes) != 4:
                raise RPCTimeoutError(
                    f"Failed to read response length header\n"
                    f"  Expected 4 bytes, got {len(length_bytes)}\n"
                    f"  Method: {method}"
                )

            response_length = struct.unpack('>I', length_bytes)[0]
        except struct.error as e:
            raise RPCError(
                f"Invalid response length header\n"
                f"  Method: {method}\n"
                f"  Error: {e}"
            )

        # Read response payload
        try:
            response_bytes = self.process.stdout.read(response_length)
            if len(response_bytes) != response_length:
                raise RPCTimeoutError(
                    f"Failed to read complete response\n"
                    f"  Expected {response_length} bytes, got {len(response_bytes)}\n"
                    f"  Method: {method}"
                )

            response = msgpack.unpackb(response_bytes, raw=False)
        except Exception as e:
            raise RPCError(
                f"Failed to deserialize response\n"
                f"  Method: {method}\n"
                f"  Error: {e}"
            )

        # Handle error response
        if "e" in response:
            raise RPCError(
                f"Remote method raised exception: {method}\n"
                f"  Error: {response['e']}"
            )

        # Handle success response
        if "r" not in response:
            raise RPCError(
                f"Invalid response format (missing 'r' key)\n"
                f"  Method: {method}\n"
                f"  Response: {response}"
            )

        return response["r"]

    def close(self) -> None:
        """Terminate subprocess and cleanup resources."""
        if self.process is not None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            finally:
                self.process = None

    def load(self) -> Any:
        """
        Create proxy object for RPC method calls.

        Returns:
            Proxy object that forwards method calls to RPC server
        """
        bridge = self

        class RPCProxy:
            """Proxy object that forwards method calls via RPC."""

            def __getattr__(self, name: str):
                """
                Create callable for any attribute access.

                Args:
                    name: Method name

                Returns:
                    Callable that invokes RPC method
                """
                def call_method(**kwargs):
                    """
                    Invoke RPC method.

                    Args:
                        **kwargs: Method arguments

                    Returns:
                        Result from remote method
                    """
                    return bridge.call(name, **kwargs)

                return call_method

        return RPCProxy()

    def __enter__(self) -> "RPCBridge":
        """Context manager support."""
        return self

    def __exit__(self, *args) -> None:
        """Cleanup on context exit."""
        self.close()
