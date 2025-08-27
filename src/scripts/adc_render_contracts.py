#!/usr/bin/env python3
"""
ADC Contract Tree Renderer - Simplified Implementation
Renders .qmd files to PDF while preserving directory structure
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import argparse

class ContractTreeRenderer:
    """Render Quarto contract files to PDF with parallel directory structure"""
    
    TEMP_EXTENSIONS = [
        '.aux', '.log', '.out', '.toc', '.lof', '.lot', 
        '.bbl', '.blg', '.fls', '.fdb_latexmk', '.synctex.gz',
        '.tex', '.bcf', '.run.xml'
    ]
    
    def __init__(self):
        """Initialize renderer"""
        self.stats = {'success': 0, 'failed': 0, 'skipped': 0}
        self.errors = []
        
    def check_quarto(self):
        """Check if Quarto is installed"""
        try:
            result = subprocess.run(['quarto', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def find_qmd_files(self, source_dir):
        """Find all .qmd files in directory tree"""
        qmd_files = []
        for qmd_file in Path(source_dir).rglob('*.qmd'):
            qmd_files.append(qmd_file)
        return sorted(qmd_files)
    
    def render_file(self, qmd_file, output_pdf):
        """Render a single .qmd file to PDF"""
        # Ensure output directory exists
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        
        # Build command - render in place
        cmd = [
            'quarto', 'render', qmd_file.name,
            '--to', 'pdf'
        ]
        
        # Save current directory
        original_cwd = os.getcwd()
        
        try:
            # Change to the file's directory for rendering
            os.chdir(qmd_file.parent)
            
            # Run render command
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                # Move the generated PDF to the target location
                generated_pdf = qmd_file.parent / (qmd_file.stem + '.pdf')
                if generated_pdf.exists():
                    shutil.move(str(generated_pdf), str(output_pdf))
                    return True, None
                else:
                    return False, "PDF not generated"
            else:
                return False, result.stderr
                
        except Exception as e:
            return False, str(e)
        finally:
            # Always restore the original directory
            os.chdir(original_cwd)
    
    def clean_temp_files(self, directory):
        """Remove temporary files"""
        # Remove files by extension
        for ext in self.TEMP_EXTENSIONS:
            for temp_file in Path(directory).rglob(f'*{ext}'):
                try:
                    temp_file.unlink()
                except:
                    pass
        
        # Remove Quarto cache directories
        for temp_dir in Path(directory).rglob('*_files'):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    def render_tree(self, source_dir, output_dir):
        """Main rendering function"""
        source_path = Path(source_dir).resolve()
        output_path = Path(output_dir).resolve()
        
        # Check Quarto
        print("🔍 Checking for Quarto installation...")
        if not self.check_quarto():
            print("❌ Quarto not found!")
            print("   Install from: https://quarto.org/docs/get-started/")
            print("   Or via homebrew: brew install quarto")
            return False
        print("✅ Quarto found")
        
        # Find files
        print(f"\n📂 Scanning: {source_path}")
        qmd_files = self.find_qmd_files(source_path)
        
        if not qmd_files:
            print("❌ No .qmd files found")
            return False
        
        print(f"✅ Found {len(qmd_files)} .qmd files")
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Render each file
        print(f"\n🔄 Rendering to: {output_path}")
        for i, qmd_file in enumerate(qmd_files, 1):
            # Calculate paths
            rel_path = qmd_file.relative_to(source_path)
            pdf_name = qmd_file.stem + '.pdf'
            output_pdf = output_path / rel_path.parent / pdf_name
            
            print(f"\n[{i}/{len(qmd_files)}] {rel_path}")
            
            success, error = self.render_file(qmd_file, output_pdf)
            
            if success:
                print(f"  ✅ → {output_pdf.relative_to(output_path)}")
                self.stats['success'] += 1
            else:
                print(f"  ❌ Failed")
                if error:
                    print(f"     {error.splitlines()[0]}")
                self.stats['failed'] += 1
                self.errors.append({
                    'file': str(rel_path),
                    'error': error
                })
        
        # Clean up
        print(f"\n🧹 Cleaning temporary files...")
        self.clean_temp_files(source_path)
        
        # Summary
        print(f"\n✨ Rendering complete!")
        print(f"   ✅ Success: {self.stats['success']}")
        print(f"   ❌ Failed: {self.stats['failed']}")
        
        # Save error log if needed
        if self.errors:
            error_log = output_path / 'rendering_errors.txt'
            with open(error_log, 'w') as f:
                for error in self.errors:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"File: {error['file']}\n")
                    f.write(f"Error:\n{error['error']}\n")
            print(f"\n📋 Error details saved to: {error_log}")
        
        return self.stats['failed'] == 0

def main():
    parser = argparse.ArgumentParser(
        description='Render .qmd contract files to PDF'
    )
    parser.add_argument('source', help='Source directory containing .qmd files')
    parser.add_argument('output', help='Output directory for PDFs')
    
    args = parser.parse_args()
    
    renderer = ContractTreeRenderer()
    success = renderer.render_tree(args.source, args.output)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()