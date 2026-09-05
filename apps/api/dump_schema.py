import sys
from pathlib import Path
sys.path.append(str(Path("d:/working_projects/razorpay/razorgrowth-ai/apps/api").resolve()))

import json
from app.main import app

with open("openapi_schema.json", "w") as f:
    json.dump(app.openapi(), f, indent=2)
print("Schema generated")
