# Secret setup in azure
## Access secrets in deployment (managed identity)
### Step 1 — Enable System-Assigned Managed Identity

1. Open your **Function App** in the [Azure Portal](https://portal.azure.com).
2. In the left menu, select **Identity**.
3. Under the **System assigned** tab:
    - Set **Status** to **On**.
    - Click **Save**.

---

### Step 2 — Grant Key Vault Access via RBAC
1. Open your **Key Vault** in the Azure Portal.
2. Go to **Access control (IAM)** → **+ Add → Add role assignment**.
3. Configure the role assignment:
- **Role:** `Key Vault Secrets User`
- **Assign access to:** *Managed identity*
- **Select members:**
    - Choose your **Subscription**.
    - Select your **Function App** (or its system-assigned identity).
4. Click **Review + assign** to confirm.

---

### Step 3 — Restart the Function App
1. Return to your **Function App → Overview**.
2. Click **Restart**.

> This ensures the app picks up its new managed identity environment variables.
