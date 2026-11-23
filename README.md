# AwareML

### Transparent, Controllable, and Sustainable Streaming AutoML

AwareML is an interactive research system for exploring, selecting, running, and evaluating automated machine learning frameworks on streaming classification tasks. It brings predictive performance, computational efficiency, sustainability, fairness, and explainability into a shared workspace.

Users can describe their requirements in natural language, review framework recommendations, run streaming experiments, inspect supporting evidence, and make their own decisions. The system connects automated analysis with human review throughout the workflow.

This repository contains the extended AwareML application, framework integrations, recommendation components, scenario benchmarks, evaluation resources, and research scripts.

**Repository:** [DataSystemsGroupUT/AwareMLExtension](https://github.com/DataSystemsGroupUT/AwareMLExtension)

## Overview

Selecting a streaming AutoML framework involves several competing considerations. A framework with strong predictive accuracy may require more processing time or energy, while an efficient alternative may offer a different balance of performance and resource consumption.

AwareML helps users examine these trade-offs through:

- Natural-language interpretation of deployment objectives.
- Dataset-aware and historical framework recommendations.
- Streaming execution and temporal performance analysis.
- Multiobjective comparison and interactive visualizations.
- Fairness, explainability, and sustainability diagnostics.
- Evidence-grounded explanations and human review.
- Experiment exports and evaluation resources.

The application maintains a shared dataset and experiment context across its workspaces so users can move between configuration, recommendation, execution, and analysis.

## Main Capabilities

### Natural-Language Goal Interpretation

The Copilot interprets deployment requirements expressed in natural language and maps them to supported optimization objectives:

- Accuracy.
- Runtime.
- Energy consumption.
- CO₂ emissions.

Users can inspect the interpreted objectives and review their preferences before using a recommendation.

### Framework Recommendation

AwareML provides two complementary recommendation approaches:

- **Dataset-aware recommendation:** uses dataset characteristics and objective preferences to estimate framework suitability.
- **Historical recommendation:** uses previously collected benchmark evidence to support preference-based selection when a dataset is unavailable.

Recommendations are presented alongside their evidence and assumptions.

### Streaming Experimentation

The experiment engine supports sequential evaluation of streaming classifiers and inspection of performance over time. Users can configure the dataset, target, sensitive attribute, evaluation window, and execution settings.

### Multiobjective Decision Support

Interactive views help users compare alternatives across performance and resource objectives, inspect rankings, and explore trade-offs.

### Responsible AI Analysis

The application combines fairness diagnostics, explainability tools, sustainability measurements, and explanation-integrity checks within the experiment workflow.

### Human Review

Users remain responsible for the final selection. They can inspect recommendations, compare alternatives, and accept, override, or reject assistant proposals in the relevant workflows.

## Supported Frameworks

AwareML integrates five streaming AutoML frameworks:

| Framework | Integration |
|---|---|
| AutoStreamML | Streaming AutoML adapter |
| AutoClass | Streaming classification adapter |
| EvoAutoML | Evolutionary streaming AutoML adapter |
| OAML | Online AutoML adapter |
| ChaCha | Online model-selection adapter |

The adapters are maintained in `awareml/frameworks/`.

OAML and EvoAutoML use separate Python environments to accommodate their dependency requirements. Their workers are connected to the main application through configured interpreter paths.

## Application Workspaces

| Workspace | Purpose |
|---|---|
| **Command Centre** | Review the active context and application status. |
| **Run Studio** | Load data, configure a streaming experiment, and execute frameworks. |
| **3D Decision Space** | Explore framework recommendations and multiobjective trade-offs. |
| **Responsible AI** | Inspect fairness, explainability, and sustainability evidence. |
| **Goal and Recommendaion Plan** | Describe goals, review interpreted objectives, and examine recommendations. |
| **Explanation Integrity Lab** | Examine explanation support, consistency, and diagnostic evidence. |
| **Export Center** | Export experiment results and reproducibility resources. |
| **Advanced Labs** | Access additional research and study interfaces. |

The available analyses depend on the active dataset, completed runs, installed backends, and available model artifacts.

## System Workflow

1. **Load a dataset.** Use a supported dataset or provide a CSV file.
2. **Configure the task.** Select the target, optional sensitive attribute, positive label, and streaming settings.
3. **Specify objectives.** Describe the deployment goal or review the objective preferences directly.
4. **Inspect recommendations.** Compare the suggested framework with alternatives and review the supporting evidence.
5. **Run the experiment.** Execute the selected configuration using the streaming evaluation engine.
6. **Analyse outcomes.** Inspect predictive performance, temporal behaviour, fairness, explanations, and resource consumption.
7. **Review the decision.** Use the available evidence to confirm or revise the selection.
8. **Export results.** Save the experiment outputs and associated configuration.

## Repository Organization

The main application components are organized as follows:

| Path | Contents |
|---|---|
| `app.py` | Main Streamlit application entry point. |
| `awareml/` | Application and research implementation. |
| `awareml/analysis/` | Analysis utilities. |
| `awareml/engine/` | Streaming execution and evaluation components. |
| `awareml/experiments/` | Experiment definitions, dataset registries, and orchestration. |
| `awareml/frameworks/` | Framework adapters and registry. |
| `awareml/recommender/` | Recommendation models, schemas, and ranking logic. |
| `awareml/llm/` | Language-model integration. |
| `awareml/explanation_integrity/` | Explanation verification and integrity components. |
| `awareml/faithfulness/` | Faithfulness evaluation utilities. |
| `awareml/studies/` | Study runtime and data handling. |
| `awareml/ui/` | Shared interface components. |
| `awareml/ui_v2/` | Dashboard workspaces and interface implementation. |
| `awareml/workers/` | Backend worker processes. |
| `configs/` | Dataset and research configuration files. |
| `data/demo/` | Demonstration resources. |
| `data/journal/` | Research benchmarks and evaluation resources. |
| `data/llm/` | Language-model-related resources. |
| `data/meta/` | Meta-learning resources and dataset manifests. |
| `data/stream_datasets/` | Streaming dataset resources. |
| `scripts/` | Execution, evaluation, analysis, and validation scripts. |
| `hpc/` | High-performance computing resources. |
| `tests/` | Automated tests. |
| `.env.example` | Example local configuration. |
| `requirements.txt` | Main environment dependencies. |
| `requirements-optional.txt` | Additional research dependencies. |
| `requirements-oaml.txt` | OAML environment dependencies. |
| `requirements-evo.txt` | EvoAutoML environment dependencies. |
| `requirements-dev.txt` | Development dependencies. |

## Installation

### Requirements

The repository specifies **CPython 3.8.10**, with Python compatibility constrained to `>=3.8.10,<3.9`.

The supplied setup scripts use Windows PowerShell and the Python launcher. Install Git and the required Python interpreter before running them.

Some native dependencies may require platform-specific build tools.

### Clone the Repository

```bash
git clone https://github.com/DataSystemsGroupUT/AwareMLExtension.git
cd AwareMLExtension
```

### Create the Application Environments

Run the supplied setup scripts in PowerShell:

```powershell
.\setup.ps1
.\setup_oaml.ps1
.\setup_evo.ps1
```

These scripts create:

| Environment | Purpose |
|---|---|
| `.venv` | Dashboard, analysis tools, and main backends. |
| `.venv-oaml` | Isolated OAML backend. |
| `.venv-evo` | Isolated EvoAutoML backend. |

The scripts install the corresponding dependencies and perform import checks.

### Create the Local Configuration

Copy the example configuration:

```powershell
Copy-Item .env.example .env
```

Review the values before starting the application.

### Start AwareML

```powershell
.\run.ps1
```

The launcher configures the isolated backend interpreter paths and starts the Streamlit application.

To launch the main application directly:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

When launching directly, ensure the backend interpreter paths are configured in `.env`.

## Configuration

AwareML reads local settings from environment variables and `.env`.

| Variable | Purpose |
|---|---|
| `OLLAMA_BASE_URL` | Address of the local Ollama service. |
| `OLLAMA_MODEL` | Model tag used by the language-model integration. |
| `AWAREML_COUNTRY_ISO` | Country code used for sustainability configuration. |
| `AWAREML_STUDY_DB` | Location of the study database. |
| `AWAREML_OAML_PYTHON` | Python interpreter for the isolated OAML environment. |
| `AWAREML_EVO_PYTHON` | Python interpreter for the isolated EvoAutoML environment. |
| `AWAREML_OAML_MODE` | OAML execution mode. |
| `AWAREML_LLM_ENABLED` | Enables language-model integration where supported. |
| `AWAREML_CODECARBON_ENABLED` | Enables CodeCarbon integration where supported. |

### Local Language Model

The example configuration uses an Ollama service:

```dotenv
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
AWAREML_LLM_ENABLED=true
```

Install Ollama and download the model selected in your configuration:

```bash
ollama pull llama3.1:8b
```

Ensure the service is running and reachable at `OLLAMA_BASE_URL`. Model availability and hardware requirements depend on the chosen model.

### Sustainability Settings

Example configuration:

```dotenv
AWAREML_COUNTRY_ISO=EST
AWAREML_CODECARBON_ENABLED=true
```

Use the country configuration appropriate for the execution environment.

## Quick Start

### Run a Demonstration

1. Start AwareML and open **Run Studio**.
2. Select **Upload dataset**.
3. Set:
   - Target: `target`.
   - Sensitive attribute: `group`.
   - Positive label: ``.
4. Review the experiment settings and run the experiment.
5. Inspect the resulting performance and responsible AI analyses.
6. Open **Goal and Recommendaion Plan** to explore goal interpretation and recommendation.
7. Use **Export Center** to export the available results.

### Use Your Own Dataset

Prepare a CSV file containing the input features and target column. Include a sensitive attribute if group-based fairness analysis is required.

After loading the file:

1. Select the target column.
2. Select the sensitive attribute and positive label where applicable.
3. Check missing values, feature types, and class distribution.
4. Review the row order used for streaming evaluation.
5. Configure the evaluation window and execution settings.
6. Run the experiment and inspect its outputs.

For time-ordered datasets, preserve the intended temporal order when preparing the CSV.

## Recommendations and Evidence

AwareML separates information used before execution from outcomes observed during an experiment.

| Evidence | Interpretation |
|---|---|
| Dataset profile | Characteristics extracted from the available data. |
| Historical benchmark evidence | Previously observed framework outcomes. |
| Predicted framework outcomes | Estimates produced by a recommendation model. |
| Observed run outcomes | Measurements collected during the current experiment. |
| Generated explanation | A natural-language account that should be checked against its supporting evidence. |

### Dataset-Aware Recommendation

The dataset-aware recommender combines dataset characteristics with the selected objectives to estimate framework suitability.

Its availability depends on the required model artifacts and compatible dependencies.

### Historical Recommendation

The historical recommender supports preference-based comparison using previously collected benchmark evidence. It can assist exploration before a dataset is supplied.

Historical performance provides context; it does not establish how a framework will perform on a new stream.

### Objective Preferences

Accuracy is treated as a benefit objective. Runtime, energy consumption, and CO₂ emissions are treated as cost objectives.

Users should inspect the selected objectives, their weights, and the available evidence before relying on a ranking.

## Fairness, Explainability, and Sustainability

### Fairness

Fairness analyses use the configured sensitive attribute and prediction outcomes to examine group-level differences.

Interpret the results in relation to:

- The prediction task.
- The selected positive label.
- Group sizes and class distributions.
- The evaluation window.
- Changes in the stream over time.

### Explainability

AwareML includes model diagnostics and explanation tools supported by the installed dependencies.

SHAP and LIME are included in the additional research requirements. The applicable methods depend on the framework, model interface, and available experiment evidence.

### Explanation Integrity

The Explanation Integrity Lab supports inspection of whether explanation claims agree with the underlying evidence.

Users can examine numerical claims, framework comparisons, and the relationship between an explanation and the results it describes.

### Sustainability

CodeCarbon integration supports energy and CO₂ estimation.

Energy consumption and emissions depend on the execution environment and measurement assumptions. Report hardware, configuration, and estimation settings when comparing results across systems.

## Benchmarks and Evaluation Data

The repository includes resources for studying:

- Natural-language objective selection.
- Framework recommendation and multiobjective ranking.
- Explanation correctness and faithfulness.
- Fairness and sustainability analysis.
- Trust calibration.
- Information seeking during AI-assisted decisions.

Research resources are primarily located in:

- `data/journal/`
- `data/meta/`
- `configs/`
- `scripts/`
- `hpc/`

Consult the configuration and input requirements of each experiment before running it. Some analyses require previously generated artifacts or datasets obtained separately.

## Reproducibility

When reporting or reproducing an experiment, record:

- Repository commit.
- Python and dependency versions.
- Dataset identity and preprocessing.
- Stream order and processed instance count.
- Target, sensitive attribute, and positive label.
- Framework configuration and random seeds.
- Evaluation window and stopping conditions.
- Objective weights and ranking procedure.
- Hardware and resource-measurement settings.
- Language-model identifier and generation settings, where applicable.

Distinguish predicted outcomes from observed measurements and report incomplete runs explicitly.

Use the same evaluation conditions across frameworks when making comparative claims.

## Development and Validation

Install the development dependencies in the main environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Run the project structure validation:

```powershell
.\.venv\Scripts\python.exe -m scripts.validate_project
```

Run the automated tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Some tests and research scripts require additional backends, local services, or generated benchmark artifacts.

## Contributing

Contributions are welcome through issues and pull requests.

For a bug report, include:

- A clear description of the problem.
- Steps to reproduce it.
- The repository commit and Python version.
- Relevant configuration and framework.
- A minimal dataset example where possible.
- Relevant error output.

For implementation changes, describe the resulting behaviour and provide validation appropriate to the change.

Avoid committing credentials, local environment files, or participant-identifiable data.

## Research Use and Acknowledgements

AwareML supports research on streaming AutoML, responsible AI, and human–AI decision support.

When using the system in academic work, cite the associated AwareML publication and acknowledge the underlying frameworks, datasets, and software packages used in the experiment.

The project is associated with the **Data Systems Group, Institute of Computer Science, University of Tartu**.

For questions, bug reports, and feature requests, use the [repository issue tracker](https://github.com/DataSystemsGroupUT/AwareMLExtension/issues).
