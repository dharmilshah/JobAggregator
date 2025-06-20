from flask import Flask, jsonify
import jobaggregator  # your main script imported as module

app = Flask(__name__)

@app.route('/run-jobs', methods=['GET'])
def run_jobs():
    try:
        results = jobaggregator.run_job_aggregation()  # ensure your main script exposes a function
        return jsonify({"status": "success", "jobs_fetched": len(results)})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
