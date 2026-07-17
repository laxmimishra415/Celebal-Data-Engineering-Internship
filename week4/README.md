# Week 4 – Azure Cloud Fundamentals & Data Pipeline (ADF)

![Azure](https://img.shields.io/badge/Azure-0078D4?style=flat&logo=microsoftazure&logoColor=white)
![Data Factory](https://img.shields.io/badge/Azure%20Data%20Factory-0062AD?style=flat&logo=microsoftazure&logoColor=white)
![Blob Storage](https://img.shields.io/badge/Blob%20Storage-0078D4?style=flat&logo=microsoftazure&logoColor=white)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen)

## 📌 Objective
Build a complete, end-to-end cloud data pipeline on Microsoft Azure — provisioning storage, configuring Azure Data Factory (ADF), and orchestrating a metadata-validated copy pipeline (Blob → ADF → Destination).

## 🏗️ Architecture
[Superstore CSV] → [Azure Blob Storage] → [Azure Data Factory Pipeline]
├── Get Metadata (validate file)
└── Copy Data (Source → Destination)
↓
[New file in Blob Storage
## 🛠️ Tools & Services
| Category | Tool/Service |
|---|---|
| Cloud Platform | Microsoft Azure |
| Storage | Azure Blob Storage |
| Orchestration | Azure Data Factory (ADF) v2 |
| Access Management | Azure IAM (RBAC) |
| Dataset | [Superstore Dataset – Kaggle](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final) |

## ✅ Work Completed

### 1. Resource Provisioning
Created a dedicated Resource Group (`RG-Week4-DataPipeline`) in Central India to logically organize all cloud resources for this project.
📸 `screenshots/Task1_ResourceGroup.png`

### 2. Storage Layer
Provisioned a Storage Account and Blob Container, then uploaded the raw dataset — establishing the data lake landing zone for the pipeline.
📸 `screenshots/Task2_ContainerWithFile.png`

### 3. ADF Configuration
- Deployed an Azure Data Factory instance and explored the Author / Monitor / Manage interface
- Configured a **Linked Service** to securely connect ADF to Blob Storage
- Defined **Source** and **Sink Datasets** (DelimitedText/CSV) for the pipeline
- Implemented a **Get Metadata** activity to programmatically validate file attributes (name, type, size) before processing

📸 `screenshots/Task3_LinkedService.png` · `screenshots/Task3_Datasets.png` · `screenshots/Task3_GetMetadata.png`

### 4. Pipeline Orchestration
Built pipeline `PL_MetadataCheck` chaining **Get Metadata → Copy Data**, enabling automated file validation followed by data movement — a common pattern in production ETL pipelines.
📸 `screenshots/Task4_PipelineDesign.png`

### 5. Execution & Monitoring
Executed the pipeline in Debug mode and monitored the run through ADF's built-in monitoring, achieving a **Succeeded** status. Additionally, created a **Schedule Trigger (`TR_DailySchedule`)** to demonstrate pipeline scheduling and left it in the **Stopped** state to avoid automatic executions.

📸 `screenshots/Task5_PipelineSucceeded.png` · `screenshots/Task5_ExecutionDetails.png` · `screenshots/Task5_Trigger.png`

### 6. Access Control (IAM)
Configured Azure RBAC by assigning the **Storage Blob Data Contributor** role to the **Azure Data Factory Managed Identity**, enabling secure access to Blob Storage for pipeline operations.

📸 `screenshots/Task6_ManagedIdentity.png`
📸 `screenshots/Task6_IAMRoles.png`

## 🎯 Mini Project — End-to-End Validation

**Problem Statement:** Build a complete pipeline that reads a CSV file from Blob Storage and processes it using Azure Data Factory.

| Expected Output | Result |
|---|---|
| Pipeline executed successfully | ✅ Succeeded |
| Data copied to destination | ✅ `output-superstore.csv` created |
| Metadata validated | ✅ Verified via Get Metadata activity |

📸 `screenshots/MiniProject_Output.png`

## 🧩 Challenges Faced & Solutions
- **Azure Free Trial verification delays:** Initial student verification faced access issues; resolved by switching to the standard Azure free trial with card verification.
- **Destination file not generated on first run:** The `DS_DestinationCSV` dataset initially had no file name defined, so the Copy Data activity validated successfully but didn't produce an output file. Fixed by explicitly specifying an output file name in the dataset.
- **Access between ADF and Storage:** Beyond assigning IAM roles to my own account, I also granted the ADF instance's Managed Identity Contributor access on the Storage Account — reflecting the real-world pattern where the service itself (not just the user) needs authorized access to read/write data.
- **Scheduling vs. on-demand runs:** Configured a Schedule Trigger (`TR_DailySchedule`) in addition to Debug runs, to demonstrate both manual testing and automated/production-style pipeline execution.

## 💡 Key Learnings
- Provisioning and organizing Azure resources using Resource Groups
- Configuring secure connections between Azure services via Linked Services
- Designing multi-activity ADF pipelines with sequential dependencies
- Implementing metadata validation as a data quality checkpoint before transformation/movement
- Applying Azure RBAC (IAM) for scoped, secure resource access

---
*Part of the Celebal Technologies Data Engineering Internship — Week 4 of 7*
