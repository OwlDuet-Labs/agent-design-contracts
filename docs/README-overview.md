# Agentic Design Contract (ADC) Framework Overview

## Introduction

The Agentic Design Contract (ADC) framework is a system for creating machine-readable design documents that are both human-readable and AI-parsable. The goal of ADC is to simplify and accelerate software and methodology development, especially for startups, by providing a structured, verifiable way to design and build complex, agentic systems.

## Core Principles

The framework is built on three core principles:

* **Literate and DRY (Don't Repeat Yourself):** ADC is based on the principles of literate programming, where documentation is an integral part of the code. It emphasizes the DRY principle to avoid redundancy and ensure consistency between design and implementation.

* **Modularity and Parity:** The design is broken down into modular, atomic "design blocks," each with a specific type and a unique ID. These blocks have explicit "parity links" to the corresponding implementation and documentation, ensuring that the design, code, and docs are always in sync.

* **Machine-Readable and Verifiable:** ADC uses a "type system" for design concepts and a YAML front matter for metadata, making the design documents machine-readable. An "ADC checker" or "linter" can then be used to validate the design, enforce conventions, and perform semantic analysis to detect design drift automatically.

## Key Components

The ADC framework consists of several key components:

* **ADC Files:** Markdown files (`.qmd` or `.md`) that contain the design contracts.

* **ADC Conventions:** A set of rules for writing contracts, including:

    * A YAML front matter for metadata (`contract_id`, `title`, etc.).

    * Atomic and typed "design blocks" with a structured header (`### [Type: Name] <ID>`).

    * Explicit `Parity` sections to link design to code.

* **ADC Type System:** A semantic type system for design concepts, including `Rationale`, `DataModel`, `Algorithm`, `APIEndpoint`, `Constraint`, and `TestScenario`.

* **ADC Checker (Linter):** A tool to enforce ADC conventions and perform semantic analysis, which can be run in a CI/CD pipeline, on git commit hooks, or in a code editor.

* **Diagrams as Code:** The use of Mermaid.js to create diagrams directly within the design files. By embedding ADC block IDs in the diagram markup, the diagrams become verifiable and are guaranteed to be in sync with the design.

## The ADC Workflow

The ADC framework places the design contract at the center of a collaborative, agent-assisted workflow that spans product, research, and development teams. The process is divided into two main loops: an "Inner Loop" for development and an "Outer Loop" for review and publishing.

```{mermaid}
fig-width: 8.5
%%{init: {'themeVariables': { 'fontSize': '18px', 'fontFamily': 'Inter, Arial, sans-serif' }}}%%
flowchart TD
    %% Outer Loop: Cross-Disciplinary-Collaboration
    subgraph OuterLoop["OuterLoop: Cross-Disciplinary-Collaboration"]
        direction TB
        Product["Product Team"]
        Research["Research Team"]
        Dev["Development Team"]
        GitHubPR["GitHub PR (Contract + Code Review)"]
        Product -->|Collaborate| GitHubPR
        Research -->|Collaborate| GitHubPR
        Dev -->|Collaborate| GitHubPR
    end

    %% Inner Loop: Agent-Assisted-Development
    subgraph InnerLoop["InnerLoop: Agent-Assisted-Development"]
        direction LR
        PushRequestor["Push-Requestor (Human)"]
        Refiner["Refiner Agent"]
        Auditor["Auditor Agent"]
        CodeGen["Code-Gen Agent"]
        PushRequestor --> Refiner
        Refiner --> Auditor
        Auditor --> CodeGen
        CodeGen --> PushRequestor
    end

    %% Central Artifact
    ADC["ADC (Source of Truth)"]

    %% Outputs (stacked vertically)
    PublishedSoftware["Published Software"]
    PublishedDocs["Published Docs"]

    %% Connections
    Refiner -- "Reads/Writes" --> ADC
    Auditor -- "Reads" --> ADC
    CodeGen -- "Reads" --> ADC

    PushRequestor -- "Bundles Contract + Code and Submits PR" --> GitHubPR
    GitHubPR -- "On Merge" --> PublishedSoftware
    GitHubPR -- "On Merge" --> PublishedDocs

    %% ADC is central
    ADC -.-> GitHubPR

    %% adc CLI automation in review process
    adcCLI["adc CLI (Automated Checks)"]
    adcCLI -- "Automates Review" --> GitHubPR

    %% Styling
    style ADC fill:#f3e5f5,stroke:#6a1b9a,stroke-width:4px
    style GitHubPR fill:#e3f2fd,stroke:#333
    style adcCLI fill:#b3e5fc,stroke:#0288d1,stroke-width:2px
    style OuterLoop fill:#e3f2fd,stroke:#90caf9,stroke-width:2px
    style InnerLoop fill:#e3f2fd,stroke:#90caf9,stroke-width:2px

    %% Bold all nodes
    classDef boldText font-weight:bold;
    class Product,Research,Dev,GitHubPR,PushRequestor,Refiner,Auditor,CodeGen,ADC,PublishedSoftware,PublishedDocs,adcCLI boldText;
```

