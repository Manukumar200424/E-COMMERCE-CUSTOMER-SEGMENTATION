from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, redirect, render_template, request, url_for
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "ecommerce_customers.csv"
MODEL_PATH = BASE_DIR / "customer_segmentation_model.pkl"
FEATURES = [
    "AnnualIncome",
    "TotalPurchases",
    "TotalSpent",
    "AverageOrderValue",
    "PurchaseFrequency",
    "WebsiteVisits",
    "CartAdditions",
]
DISPLAY_FIELDS = [
    "CustomerID", "Gender", "Age", "AnnualIncome", "TotalPurchases",
    "TotalSpent", "AverageOrderValue", "PurchaseFrequency", "WebsiteVisits",
    "CartAdditions", "CustomerSatisfaction",
]
SEGMENT_ORDER = ["Premium / High-Value", "Regular", "Occasional", "Low-Value"]
RECOMMENDATIONS = {
    "Premium / High-Value": "Offer loyalty rewards, premium products, and exclusive discounts.",
    "Regular": "Use personalized offers and bundles to increase purchase frequency.",
    "Occasional": "Provide targeted discounts and product recommendations.",
    "Low-Value": "Use attractive offers and engagement campaigns to encourage purchases.",
}

app = Flask(__name__)


def create_dataset():
    rng = np.random.default_rng(42)
    rows = []
    for customer_id in range(1001, 1121):
        age = int(rng.integers(18, 66))
        income = int(np.clip(rng.normal(68000, 24000), 24000, 145000))
        purchases = int(np.clip(rng.poisson(13) + 1, 1, 42))
        order_value = float(np.clip(rng.normal(115, 38), 35, 260))
        spent = round(purchases * order_value, 2)
        frequency = round(float(np.clip(rng.normal(purchases / 2.1, 2.2), 0.5, 22)), 1)
        visits = int(np.clip(rng.normal(34 + frequency * 2, 12), 6, 110))
        carts = int(np.clip(rng.normal(visits * 0.27, 6), 1, 45))
        satisfaction = round(float(np.clip(rng.normal(3.8, 0.7), 1, 5)), 1)
        rows.append({
            "CustomerID": customer_id,
            "Gender": rng.choice(["Female", "Male", "Non-binary"]),
            "Age": age,
            "AnnualIncome": income,
            "TotalPurchases": purchases,
            "TotalSpent": spent,
            "AverageOrderValue": round(order_value, 2),
            "PurchaseFrequency": frequency,
            "WebsiteVisits": visits,
            "CartAdditions": carts,
            "CustomerSatisfaction": satisfaction,
        })
    pd.DataFrame(rows).to_csv(DATA_PATH, index=False)


def load_dataset():
    if not DATA_PATH.exists():
        create_dataset()
    data = pd.read_csv(DATA_PATH)
    data = data.drop_duplicates(subset="CustomerID").copy()
    for column in DISPLAY_FIELDS:
        if column not in data:
            raise ValueError(f"Dataset is missing required column: {column}")
    for column in FEATURES + ["Age", "CustomerSatisfaction"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
        data[column] = data[column].fillna(data[column].median())
    data["Gender"] = data["Gender"].fillna("Unknown")
    return data


def cluster_label(cluster_summary, cluster_id):
    scores = cluster_summary[FEATURES].copy()
    normalized = (scores - scores.min()) / (scores.max() - scores.min()).replace(0, 1)
    importance = [0.18, 0.15, 0.24, 0.12, 0.16, 0.08, 0.07]
    ranking = normalized.mul(importance, axis=1).sum(axis=1).sort_values(ascending=False)
    labels = {}
    for rank, cluster in enumerate(ranking.index):
        labels[cluster] = SEGMENT_ORDER[min(rank, len(SEGMENT_ORDER) - 1)]
    return labels[int(cluster_id)]


def build_model(data):
    scaler = StandardScaler()
    scaled = scaler.fit_transform(data[FEATURES])
    model = KMeans(n_clusters=4, random_state=42, n_init=20)
    clusters = model.fit_predict(scaled)
    data = data.copy()
    data["Cluster"] = clusters
    summary = data.groupby("Cluster")[FEATURES].mean()
    labels = {int(cluster): cluster_label(summary, int(cluster)) for cluster in summary.index}
    pca = PCA(n_components=2, random_state=42)
    coordinates = pca.fit_transform(scaled)
    artifact = {"model": model, "scaler": scaler, "pca": pca, "labels": labels, "features": FEATURES}
    joblib.dump(artifact, MODEL_PATH)
    return data, artifact, coordinates


def get_model(data):
    if MODEL_PATH.exists():
        artifact = joblib.load(MODEL_PATH)
        if artifact.get("features") == FEATURES:
            scaled = artifact["scaler"].transform(data[FEATURES])
            data = data.copy()
            data["Cluster"] = artifact["model"].predict(scaled)
            return data, artifact, artifact["pca"].transform(scaled)
    return build_model(data)


def prepare():
    data = load_dataset()
    clustered, artifact, coordinates = get_model(data)
    return clustered, artifact, coordinates


def segment_statistics(data, labels):
    rows = []
    for cluster, group in data.groupby("Cluster"):
        segment = labels[int(cluster)]
        rows.append({
            "cluster": int(cluster),
            "segment": segment,
            "customers": int(len(group)),
            "average_income": round(group["AnnualIncome"].mean(), 2),
            "average_spending": round(group["TotalSpent"].mean(), 2),
            "average_purchases": round(group["TotalPurchases"].mean(), 2),
            "average_order_value": round(group["AverageOrderValue"].mean(), 2),
            "average_frequency": round(group["PurchaseFrequency"].mean(), 2),
            "average_visits": round(group["WebsiteVisits"].mean(), 2),
            "recommendation": RECOMMENDATIONS[segment],
        })
    return sorted(rows, key=lambda row: SEGMENT_ORDER.index(row["segment"]))


def customer_records(data, labels):
    records = []
    for _, row in data.iterrows():
        records.append({
            "CustomerID": int(row["CustomerID"]),
            "Gender": row["Gender"],
            "Age": int(row["Age"]),
            "AnnualIncome": round(float(row["AnnualIncome"]), 2),
            "TotalPurchases": int(row["TotalPurchases"]),
            "TotalSpent": round(float(row["TotalSpent"]), 2),
            "AverageOrderValue": round(float(row["AverageOrderValue"]), 2),
            "PurchaseFrequency": round(float(row["PurchaseFrequency"]), 2),
            "WebsiteVisits": int(row["WebsiteVisits"]),
            "CartAdditions": int(row["CartAdditions"]),
            "CustomerSatisfaction": round(float(row["CustomerSatisfaction"]), 2),
            "Cluster": int(row["Cluster"]),
            "Segment": labels[int(row["Cluster"])],
        })
    return records


def dashboard_payload():
    data, artifact, coordinates = prepare()
    stats = segment_statistics(data, artifact["labels"])
    records = customer_records(data, artifact["labels"])
    distribution = {row["segment"]: row["customers"] for row in stats}
    spending = {row["segment"]: row["average_spending"] for row in stats}
    frequency = {row["segment"]: row["average_frequency"] for row in stats}
    scatter = [{"income": r["AnnualIncome"], "spending": r["TotalSpent"], "segment": r["Segment"]} for r in records]
    pca_points = [{"x": round(float(point[0]), 4), "y": round(float(point[1]), 4), "segment": artifact["labels"][int(cluster)]} for point, cluster in zip(coordinates, data["Cluster"])]
    wcss = []
    scaled = artifact["scaler"].transform(data[FEATURES])
    for k in range(2, 11):
        candidate = KMeans(n_clusters=k, random_state=42, n_init=10).fit(scaled)
        wcss.append({"k": k, "wcss": round(float(candidate.inertia_), 2)})
    return {
        "records": records,
        "stats": stats,
        "summary": {
            "total_customers": len(data),
            "total_segments": len(stats),
            "average_spending": round(float(data["TotalSpent"].mean()), 2),
            "average_purchases": round(float(data["TotalPurchases"].mean()), 2),
        },
        "charts": {"distribution": distribution, "spending": spending, "frequency": frequency, "scatter": scatter, "pca": pca_points, "wcss": wcss, "ages": data["Age"].value_counts().sort_index().to_dict()},
    }


@app.route("/")
def index():
    return render_template("index.html", page="dashboard")


@app.route("/segmentation")
def segmentation():
    return render_template("segmentation.html", page="segmentation")


@app.route("/customers")
def customers():
    return render_template("customers.html", page="customers")


@app.route("/visualization")
def visualization():
    return render_template("visualization.html", page="visualization")


@app.route("/about")
def about():
    return render_template("about.html", page="about")


@app.get("/api/customers")
def api_customers():
    payload = dashboard_payload()
    query = request.args.get("search", "").strip().lower()
    if query:
        payload["records"] = [r for r in payload["records"] if query in str(r["CustomerID"]).lower()]
    return jsonify(payload["records"])


@app.get("/api/segments")
def api_segments():
    return jsonify(dashboard_payload()["stats"])


@app.get("/api/statistics")
def api_statistics():
    return jsonify(dashboard_payload())


@app.post("/api/predict")
def api_predict():
    try:
        values = request.get_json(silent=True) or request.form.to_dict()
        row = {feature: float(values[feature]) for feature in FEATURES}
        row["CustomerID"] = int(values.get("CustomerID", 0) or 0)
        data, artifact, _ = prepare()
        scaled = artifact["scaler"].transform(pd.DataFrame([row], columns=FEATURES))
        cluster = int(artifact["model"].predict(scaled)[0])
        segment = artifact["labels"][cluster]
        cluster_row = next(item for item in segment_statistics(data, artifact["labels"]) if item["segment"] == segment)
        return jsonify({"cluster": cluster, "segment": segment, "spending_level": "High" if segment == SEGMENT_ORDER[0] else "Medium" if segment == SEGMENT_ORDER[1] else "Emerging", "explanation": RECOMMENDATIONS[segment], "cluster_average": cluster_row})
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({"error": f"Please provide valid values for every field. ({exc})"}), 400


@app.errorhandler(404)
def not_found(_error):
    return redirect(url_for("index"))


if __name__ == "__main__":
    prepare()
    app.run(host="127.0.0.1", port=5000, debug=True)
