from fastapi import FastAPI

app = FastAPI(title="YOLO Web App")

@app.get("/")
def read_root():
	return {"message": "YOLO Detection API is running"}

