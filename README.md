<div align="center">

# NumCraft

**Numerical Control Craftsmanship**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Framework-LangGraph_1.0-orange)](https://github.com/langchain-ai/langgraph)

**Multi-Agent Collaborative System for Intelligent G-Code Generation**

*A research-oriented framework for automated CNC machining programming*

[English](#overview) | [中文](#项目概述) | [Documentation](docs/) | [API Reference](#api-reference)

</div>

---

## Overview

NumCraft is a multi-agent collaborative system designed for intelligent G-code generation in CNC machining. Built upon LangGraph 1.0, this framework orchestrates specialized agents to automate the transformation from natural language part descriptions to executable NC programs.

### Research Context

This project explores the application of multi-agent systems in manufacturing automation, specifically addressing:
- Automated feature recognition from natural language specifications
- Collaborative decision-making in process planning
- Intelligent tool selection and parameter optimization
- Safety-critical code generation with formal verification

**Project Initiated**: March 2025

---

## Key Contributions

### 1. Multi-Agent Architecture

A novel collaborative framework comprising five specialized agents:

| Agent | Role | Key Capabilities |
|-------|------|------------------|
| **ProcessPlanner** | Feature Recognition | NLP-based feature extraction, process sequencing |
| **ToolExpert** | Tool Selection | Material-aware tool recommendation, parameter optimization |
| **PathPlanner** | Path Generation | Toolpath generation, optimization algorithms |
| **GCodeGenerator** | Code Synthesis | Standard-compliant G-code generation |
| **SafetyValidator** | Verification | Multi-layer safety checking, collision detection |

### 2. Technical Features

- **Natural Language Interface**: Accepts part descriptions in natural language
- **Feature Recognition**: Automatically identifies holes, slots, pockets, and contours
- **Material Adaptation**: Adjusts parameters based on material properties
- **Safety Verification**: Comprehensive validation of generated programs
- **FANUC Compliance**: Generates industry-standard G-code

### 3. Verified Performance

| Metric | Value | Verification Status |
|--------|-------|---------------------|
| Feature Recognition Accuracy | 85%+ | ✓ Tested |
| Safety Verification Coverage | 100% | ✓ Tested |
| Response Time (Simple Tasks) | 2-3s | ✓ Tested |
| Response Time (Complex Tasks) | 5-8s | ✓ Tested |
| Supported Features | 4 types | ✓ Implemented |

*See [Performance Verification](docs/PERFORMANCE_VERIFICATION.md) for detailed test results.*

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Input Layer                          │
│          (Natural Language Description)                 │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              ProcessPlanner Agent                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Feature   │→ │   Process    │→ │  Feasibility  │  │
│  │ Recognition │  │   Planning   │  │   Validation  │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│               ToolExpert Agent                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │    Tool     │→ │  Parameter   │→ │  Interference │  │
│  │  Selection  │  │  Optimization│  │     Check     │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              PathPlanner Agent                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Drilling  │  │   Milling    │  │     Path      │  │
│  │    Paths    │  │    Paths     │  │  Optimization │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│            GCodeGenerator Agent                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │    G-code   │→ │   Code       │→ │   Standard    │  │
│  │  Generation │  │  Optimization│  │  Conversion   │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│            SafetyValidator Agent                        │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Safety    │  │   Collision  │  │   Time        │  │
│  │   Check     │  │   Detection  │  │   Analysis    │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   Output Layer                          │
│         (G-code Program + Validation Report)            │
└─────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.12 or higher
- PostgreSQL 12+ (for memory persistence)
- LLM API access (configured via environment variables)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/numcraft.git
cd numcraft

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
export COZE_WORKLOAD_IDENTITY_API_KEY="your-api-key"
export COZE_INTEGRATION_MODEL_BASE_URL="your-base-url"
export DATABASE_URL="postgresql://user:password@localhost:5432/numcraft"
```

### Quick Start

```bash
# Start the service
python src/main.py -m http -p 5000

# Test with curl
curl -X POST http://localhost:5000/run \
  -H "Content-Type: application/json" \
  -d '{
    "part_description": "Aluminum part with a 20mm diameter hole, 30mm deep",
    "material": "6061-T6 Aluminum"
  }'
```

---

## Usage Examples

### Basic Usage

```python
import requests

response = requests.post("http://localhost:5000/run", json={
    "part_description": "Steel part with a 10mm diameter hole and a 50x30mm slot",
    "material": "45# Steel",
    "precision_requirements": {
        "hole_tolerance": "H7",
        "surface_finish": "Ra1.6"
    }
})

result = response.json()

# Access generated G-code
print(result["gcode_program"])

# Access validation report
print(result["validation_result"])
```

### Supported Features

| Feature Type | Description | Example |
|--------------|-------------|---------|
| Hole | Through holes, blind holes | "20mm diameter hole, 30mm deep" |
| Slot | Rectangular slots | "50x30mm slot, 15mm deep" |
| Pocket | Rectangular pockets | "40x40mm pocket, 20mm deep" |
| Contour | External profiles | "External contour machining" |

### Supported Materials

- Aluminum alloys (6061-T6, 7075, etc.)
- Carbon steel (45#, 1045, etc.)
- Stainless steel (304, 316, etc.)
- Custom materials (with parameter adjustment)

---

## Project Structure

```
numcraft/
├── src/
│   ├── agents/           # Agent implementations
│   │   └── agent.py      # Main agent orchestration
│   ├── tools/            # Tool definitions
│   │   ├── process_planning_tools.py
│   │   ├── tool_selection_tools.py
│   │   ├── path_planning_tools.py
│   │   ├── gcode_generation_tools.py
│   │   └── validation_tools.py
│   ├── graphs/           # Workflow definitions
│   │   ├── state.py      # State schema
│   │   └── graph.py      # Agent coordination graph
│   └── storage/          # Persistence layer
├── config/               # Configuration files
├── docs/                 # Documentation
├── examples/             # Usage examples
├── tests/                # Test suites
└── requirements.txt      # Dependencies
```

---

## API Reference

### POST /run

Execute a machining task synchronously.

**Request Body:**
```json
{
  "part_description": "string",
  "material": "string",
  "precision_requirements": {
    "hole_tolerance": "string",
    "surface_finish": "string"
  },
  "workpiece_dimensions": {
    "x_min": number,
    "x_max": number,
    "y_min": number,
    "y_max": number,
    "z_min": number,
    "z_max": number
  },
  "machine_type": "string"
}
```

**Response:**
```json
{
  "features": [...],
  "process_plan": {...},
  "tool_list": [...],
  "tool_paths": [...],
  "gcode_program": "string",
  "validation_result": {
    "is_valid": boolean,
    "errors": [...],
    "warnings": [...],
    "safety_issues": [...],
    "optimization_suggestions": [...]
  }
}
```

### POST /stream_run

Execute a machining task with streaming response (SSE format).

### POST /cancel/{run_id}

Cancel an ongoing execution.

---

## Research Applications

This framework can be extended for research in:

1. **Automated Process Planning**: Integrating with CAD systems for direct feature extraction
2. **Optimization Algorithms**: Implementing evolutionary algorithms for toolpath optimization
3. **Reinforcement Learning**: Learning optimal machining strategies from simulation
4. **Digital Twin Integration**: Real-time monitoring and adaptive control
5. **Multi-objective Optimization**: Balancing time, quality, and cost

---

## Limitations

Current version limitations (documented for transparency):

1. **Input Format**: Only natural language descriptions supported; CAD import not yet implemented
2. **Feature Complexity**: Limited to basic machining features (holes, slots, pockets, contours)
3. **Simulation**: No 3D machining simulation; validation is code-level only
4. **Controller Support**: Native FANUC format; other formats require conversion

---

## Contributing

We welcome contributions from the research community. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Code formatting
black src/
isort src/
```

---

## Citation

If you use NumCraft in your research, please cite:

```bibtex
@software{numcraft2025,
  title = {NumCraft: A Multi-Agent Collaborative System for Intelligent G-Code Generation},
  author = {NumCraft Research Team},
  year = {2025},
  month = {March},
  url = {https://github.com/yourusername/numcraft}
}
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) - State machine framework
- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework
- The CNC machining research community

---

## Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/numcraft/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/numcraft/discussions)
- **Documentation**: [docs/](docs/)

---

<div align="center">

**NumCraft - Advancing Intelligent Manufacturing**

</div>
