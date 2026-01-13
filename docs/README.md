# SDK Documentation

This directory contains all SDK documentation consolidated in one place for easy navigation.

## Documentation Structure

```
docs/
├── README.md                          # This file - Documentation index
├── architecture_overview.md          # High-level architecture overview
│
├── components/                       # Component explanations
│   ├── README.md                    # Component documentation index
│   ├── agno_agent_framework_explanation.md
│   ├── litellm_gateway_explanation.md
│   ├── rag_system_explanation.md
│   ├── cache_mechanism_explanation.md
│   ├── prompt_context_management_explanation.md
│   ├── postgresql_database_explanation.md
│   ├── evaluation_observability_explanation.md
│   ├── api_backend_services_explanation.md
│   ├── ml_framework_explanation.md
│   ├── mlops_explanation.md
│   ├── ml_data_management_explanation.md
│   ├── model_serving_explanation.md
│   ├── nats_integration_explanation.md
│   ├── otel_integration_explanation.md
│   ├── codec_integration_explanation.md
│   └── CORE_COMPONENTS_INTEGRATION_STORY.md
│
├── architecture/                    # Architecture documentation
│   ├── PROJECT_STRUCTURE.md        # Project structure
│   ├── SDK_ARCHITECTURE.md         # SDK architecture
│   ├── AI_ARCHITECTURE_DESIGN.md   # AI architecture design
│   ├── COMPONENT_CATEGORIZATION.md  # Component categorization
│   ├── COMPONENT_DEPENDENCIES.md   # Component dependencies
│   ├── EXAMPLES_AND_TESTS_SUMMARY.md # Examples and tests
│   ├── FUNCTION_DRIVEN_API.md      # Function-driven API
│   └── MISSING_COMPONENTS_ANALYSIS.md # Component analysis
│
├── troubleshooting/                 # Troubleshooting guides
│   ├── README.md                   # Troubleshooting index
│   ├── agent_troubleshooting.md
│   ├── litellm_gateway_troubleshooting.md
│   ├── rag_system_troubleshooting.md
│   ├── cache_mechanism_troubleshooting.md
│   ├── prompt_context_management_troubleshooting.md
│   ├── postgresql_database_troubleshooting.md
│   ├── evaluation_observability_troubleshooting.md
│   ├── api_backend_services_troubleshooting.md
│   ├── ml_framework_troubleshooting.md
│   ├── mlops_troubleshooting.md
│   ├── ml_data_management_troubleshooting.md
│   ├── model_serving_troubleshooting.md
│   ├── nats_integration_troubleshooting.md
│   ├── otel_integration_troubleshooting.md
│   └── codec_integration_troubleshooting.md
│
├── integration_guides/             # Integration guides
│   ├── README.md                   # Integration guides index
│   ├── nats_integration_guide.md
│   ├── otel_integration_guide.md
│   └── codec_integration_guide.md
│
├── workflows.md                     # Workflow diagrams
├── libraries.md                     # Library list
├── AI_SDK_END_TO_END_FLOW.md       # End-to-end flow documentation
├── BUILDING_NEW_USECASE_GUIDE.md    # Use case building guide
└── SDK_DEVELOPMENT_STORY.md        # Development story
```

## Quick Navigation

### Getting Started
- **Main README**: See root `README.md` for quick start
- **Developer Guide**: See root `README_DEVELOPER.md`
- **Architecture Overview**: See `architecture_overview.md`

### Component Documentation
- **Component Explanations**: See `components/` directory
- **Component README**: See `components/README.md` for index

### Architecture
- **Project Structure**: See `architecture/PROJECT_STRUCTURE.md`
- **SDK Architecture**: See `architecture/SDK_ARCHITECTURE.md`
- **AI Architecture Design**: See `architecture/AI_ARCHITECTURE_DESIGN.md`

### Troubleshooting
- **Troubleshooting Guides**: See `troubleshooting/` directory
- **Troubleshooting Index**: See `troubleshooting/README.md`

### Integration
- **Integration Guides**: See `integration_guides/` directory
- **End-to-End Flow**: See `AI_SDK_END_TO_END_FLOW.md`
- **Integration Story**: See `components/CORE_COMPONENTS_INTEGRATION_STORY.md`

### Development
- **Workflows**: See `workflows.md`
- **Libraries**: See `libraries.md`
- **Building Use Cases**: See `BUILDING_NEW_USECASE_GUIDE.md`
- **Development Story**: See `SDK_DEVELOPMENT_STORY.md`

## Documentation Types

### Component Explanations (`components/`)
Detailed documentation for each SDK component, including:
- Overview and purpose
- Core functionality
- Code examples
- Workflows
- Customization options
- Best practices

### Architecture Documentation (`architecture/`)
High-level architecture and design documentation:
- Project structure
- Component dependencies
- Architecture design
- API design

### Troubleshooting Guides (`troubleshooting/`)
Problem-solving guides for common issues:
- Error diagnosis
- Resolution steps
- Best practices
- Common pitfalls

### Integration Guides (`integration_guides/`)
Guides for integrating platform components:
- NATS integration
- OTEL integration
- CODEC integration

## Contributing to Documentation

When adding or updating documentation:
1. Place component explanations in `components/`
2. Place architecture docs in `architecture/`
3. Place troubleshooting guides in `troubleshooting/`
4. Update this README if adding new sections
5. Follow existing documentation structure and style

