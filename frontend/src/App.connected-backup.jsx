import { useEffect, useMemo, useState } from "react";
import {
  LayoutDashboard,
  Search,
  BarChart3,
  History,
  BrainCircuit,
  ShieldCheck,
  ShieldAlert,
  Activity,
  Users,
  AlertTriangle,
  CheckCircle2,
  ArrowUpRight,
  Sparkles,
  FileText,
  Zap,
  RefreshCcw,
  Filter,
  X,
  Download,
  Eye,
  ChevronRight,
} from "lucide-react";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts";

import "./App.css";


const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const EMPTY_HISTORY = [];

function App() {
  const [activePage, setActivePage] = useState("Dashboard");
  const [demoSamples, setDemoSamples] = useState([]);
  const [selectedDemoId, setSelectedDemoId] = useState("");
  const [apiStatus, setApiStatus] = useState("checking");
  const [apiError, setApiError] = useState("");
  const [result, setResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [categoryFilter, setCategoryFilter] = useState("All");

  const history = EMPTY_HISTORY;

  const analyticsData = [
    { name: "Mon", safe: 68, suspicious: 22 },
    { name: "Tue", safe: 74, suspicious: 28 },
    { name: "Wed", safe: 61, suspicious: 31 },
    { name: "Thu", safe: 82, suspicious: 25 },
    { name: "Fri", safe: 91, suspicious: 36 },
    { name: "Sat", safe: 76, suspicious: 29 },
    { name: "Sun", safe: 88, suspicious: 34 },
  ];

  const categoryData = [
    { name: "Electronics", value: 32 },
    { name: "Fashion", value: 24 },
    { name: "Beauty", value: 17 },
    { name: "Home", value: 15 },
    { name: "Other", value: 12 },
  ];

  const trendData = [
    { day: "01", risk: 38 },
    { day: "02", risk: 42 },
    { day: "03", risk: 35 },
    { day: "04", risk: 51 },
    { day: "05", risk: 48 },
    { day: "06", risk: 62 },
    { day: "07", risk: 57 },
    { day: "08", risk: 68 },
    { day: "09", risk: 61 },
  ];

  const filteredHistory = useMemo(() => {
    return history.filter((record) => {
      const search = searchTerm.toLowerCase().trim();

      const matchesSearch =
        !search ||
        record.id.toLowerCase().includes(search) ||
        record.category.toLowerCase().includes(search);

      const matchesStatus =
        statusFilter === "All" || record.status === statusFilter;

      const matchesCategory =
        categoryFilter === "All" || record.category === categoryFilter;

      return matchesSearch && matchesStatus && matchesCategory;
    });
  }, [history, searchTerm, statusFilter, categoryFilter]);

  const suspiciousCount = history.filter(
    (item) => item.status === "Suspicious"
  ).length;

  const safeCount = history.filter((item) => item.status === "Safe").length;

  useEffect(() => {
    let isCurrent = true;

    fetch(`${API_BASE_URL}/health`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Health check failed (${response.status}).`);
        }
        return response.json();
      })
      .then((health) => {
        if (isCurrent) {
          setApiStatus(
            health.status === "ok" &&
              health.model_loaded &&
              health.scaler_loaded &&
              health.demo_samples_loaded
              ? "online"
              : "offline"
          );
        }
      })
      .catch(() => {
        if (isCurrent) {
          setApiStatus("offline");
        }
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  useEffect(() => {
    if (activePage !== "Detection") {
      return undefined;
    }

    let isCurrent = true;
    fetch(`${API_BASE_URL}/demo-samples`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Could not load demo samples (${response.status}).`);
        }
        return response.json();
      })
      .then((samples) => {
        if (!Array.isArray(samples) || samples.length === 0) {
          throw new Error("The API returned no YelpChi demo samples.");
        }
        if (isCurrent) {
          setApiError("");
          setDemoSamples(samples);
          setSelectedDemoId((currentId) =>
            samples.some((sample) => String(sample.id) === currentId)
              ? currentId
              : String(samples[0].id)
          );
        }
      })
      .catch((error) => {
        if (isCurrent) {
          setApiError(
            `${error.message} Start the backend at http://127.0.0.1:8000.`
          );
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [activePage]);

  const selectedDemo = demoSamples.find(
    (sample) => String(sample.id) === selectedDemoId
  );

  const analyzeDemoSample = async () => {
    if (!selectedDemo) {
      setApiError("Select a dataset sample before running the model.");
      return;
    }

    setIsAnalyzing(true);
    setApiError("");
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ features: selectedDemo.features }),
      });
      const prediction = await response.json();
      if (!response.ok) {
        throw new Error(prediction.detail || `Prediction failed (${response.status}).`);
      }
      setResult({ ...prediction, sample: selectedDemo });
    } catch (error) {
      setApiError(
        `${error.message} Check that the backend is running and see its terminal for details.`
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const resetFilters = () => {
    setSearchTerm("");
    setStatusFilter("All");
    setCategoryFilter("All");
  };

  const exportHistory = () => {
    const header = "Seller ID,Category,Risk Score,Status,Date,Reviews\n";

    const rows = filteredHistory
      .map(
        (item) =>
          `${item.id},${item.category},${item.score},${item.status},${item.date},${item.reviews}`
      )
      .join("\n");

    const blob = new Blob([header + rows], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "detection-history.csv";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  const navigation = [
    { name: "Dashboard", icon: LayoutDashboard },
    { name: "Detection", icon: Search },
    { name: "Analytics", icon: BarChart3 },
    { name: "History", icon: History },
    { name: "Model", icon: BrainCircuit },
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <ShieldCheck size={24} />
          </div>

          <div>
            <h2>Trustline</h2>
            <span>Seller Intelligence</span>
          </div>
        </div>

        <div className="ai-status">
          <div
            className={`status-dot ${apiStatus === "online" ? "" : "offline"}`}
          ></div>

          <div>
            <strong>
              {apiStatus === "online"
                ? "Model API Online"
                : apiStatus === "checking"
                  ? "Checking Model API"
                  : "Model API Offline"}
            </strong>
            <span>YelpChi dataset demo</span>
          </div>
        </div>

        <nav className="navigation">
          <p className="nav-title">MAIN MENU</p>

          {navigation.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.name}
                className={`nav-item ${
                  activePage === item.name ? "active" : ""
                }`}
                onClick={() => setActivePage(item.name)}
              >
                <Icon size={19} />

                <span>{item.name}</span>

                {activePage === item.name && (
                  <ChevronRight className="nav-arrow" size={16} />
                )}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <div className="model-mini-card">
            <div className="mini-icon">
              <BrainCircuit size={18} />
            </div>

            <div>
              <strong>PyTorch MLP</strong>
              <span>32 numerical features</span>
            </div>
          </div>

          <p className="copyright">
            YelpChi model demonstration
            <br />
            © 2026 Trustline
          </p>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="breadcrumb">DATASET MODEL DEMO</p>
            <h1>{activePage}</h1>
          </div>

          <div className="topbar-right">
            <div className="live-indicator">
              <span></span>
              Dataset Demo
            </div>

            <div className="profile">
              <div className="profile-avatar">SK</div>

              <div>
                <strong>Admin</strong>
                <span>AI Analyst</span>
              </div>
            </div>
          </div>
        </header>

        {activePage === "Dashboard" && (
          <section className="page">
            <div className="hero-card">
              <div className="hero-content">
                <div className="hero-badge">
                  <Sparkles size={15} />
                  AI-POWERED DETECTION
                </div>

                <h2>
                  Explore the YelpChi
                  <br />
                  model demo.
                </h2>

                <p>
                  Run a transparent dataset demo using the packaged YelpChi
                  model. Seller-specific analysis is not available.
                </p>

                <button
                  className="primary-button hero-button"
                  onClick={() => setActivePage("Detection")}
                >
                  Start Detection
                  <ArrowUpRight size={18} />
                </button>
              </div>

              <div className="hero-visual">
                <div className="orb orb-one"></div>
                <div className="orb orb-two"></div>

                <div className="shield-large">
                  <ShieldCheck size={64} />
                </div>

                <div className="floating-card floating-one">
                  <CheckCircle2 size={18} />
                  <span>Dataset sample</span>
                </div>

                <div className="floating-card floating-two">
                  <Zap size={18} />
                  <span>Model inference</span>
                </div>
              </div>
            </div>

            <div className="section-heading">
              <div>
                <p className="eyebrow">OVERVIEW</p>
                <h2>Detection intelligence</h2>
              </div>

              <span className="demo-label">
                ILLUSTRATIVE DATA — NOT MODEL RESULTS
              </span>
            </div>

            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-top">
                  <div className="stat-icon blue">
                    <Users size={21} />
                  </div>

                  <span className="stat-change neutral">ILLUSTRATIVE</span>
                </div>

                <span className="stat-label">Sellers analyzed</span>
                <strong className="stat-number">—</strong>
                <span className="stat-description">Not collected</span>
              </div>

              <div className="stat-card">
                <div className="stat-top">
                  <div className="stat-icon red">
                    <ShieldAlert size={21} />
                  </div>

                  <span className="stat-change neutral">ILLUSTRATIVE</span>
                </div>

                <span className="stat-label">Suspicious assessments</span>
                <strong className="stat-number">—</strong>
                <span className="stat-description">No seller assessment</span>
              </div>

              <div className="stat-card">
                <div className="stat-top">
                  <div className="stat-icon green">
                    <ShieldCheck size={21} />
                  </div>

                  <span className="stat-change neutral">ILLUSTRATIVE</span>
                </div>

                <span className="stat-label">Safe assessments</span>
                <strong className="stat-number">—</strong>
                <span className="stat-description">No seller assessment</span>
              </div>

              <div className="stat-card">
                <div className="stat-top">
                  <div className="stat-icon purple">
                    <BrainCircuit size={21} />
                  </div>

                  <span className="stat-change neutral">MODEL</span>
                </div>

                <span className="stat-label">Model inputs</span>
                <strong className="stat-number">32</strong>
                <span className="stat-description">Numerical features</span>
              </div>
            </div>

            <div className="dashboard-grid">
              <div className="panel large-panel">
                <div className="panel-header">
                  <div>
                    <p className="eyebrow">ACTIVITY</p>
                    <h3>Detection overview</h3>
                  </div>

                  <span className="panel-tag">Last 7 days</span>
                </div>

                <div className="chart-wrapper">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={analyticsData}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        vertical={false}
                      />

                      <XAxis dataKey="name" />

                      <YAxis />

                      <Tooltip />

                      <Bar
                        dataKey="safe"
                        name="Safe"
                        fill="#79c9a4"
                        radius={[6, 6, 0, 0]}
                      />

                      <Bar
                        dataKey="suspicious"
                        name="Suspicious"
                        fill="#e995a7"
                        radius={[6, 6, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <div>
                    <p className="eyebrow">RISK DISTRIBUTION</p>
                    <h3>Seller categories</h3>
                  </div>
                </div>

                <div className="pie-container">
                  <ResponsiveContainer width="100%" height={230}>
                    <PieChart>
                      <Pie
                        data={categoryData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={85}
                      >
                        {categoryData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={
                              [
                                "#8da8e8",
                                "#d9a5bc",
                                "#9bcbb7",
                                "#e9c78b",
                                "#b7a8d9",
                              ][index]
                            }
                          />
                        ))}
                      </Pie>

                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="legend-list">
                  {categoryData.map((item, index) => (
                    <div className="legend-item" key={item.name}>
                      <span
                        className="legend-dot"
                        style={{
                          background: [
                            "#8da8e8",
                            "#d9a5bc",
                            "#9bcbb7",
                            "#e9c78b",
                            "#b7a8d9",
                          ][index],
                        }}
                      ></span>

                      <span>{item.name}</span>
                      <strong>{item.value}%</strong>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>
        )}

        {activePage === "Detection" && (
          <section className="page">
            <div className="page-intro">
              <div>
                <p className="eyebrow">DATASET DEMO</p>
                <h2>Run a YelpChi sample</h2>
                <p>
                  Select one of the packaged 32-feature samples and send it
                  unchanged through the scaler and classifier.
                </p>
              </div>

              <div className="engine-status">
                <span className={apiStatus === "online" ? "" : "offline"}></span>
                {apiStatus === "online"
                  ? "API Ready"
                  : apiStatus === "checking"
                    ? "Checking API"
                    : "API Offline"}
              </div>
            </div>

            <div className="detection-layout">
              <div className="panel detection-form">
                <div className="panel-header">
                  <div>
                    <p className="eyebrow">PACKAGED TEST DATA</p>
                    <h3>Choose a sample</h3>
                  </div>

                  <BrainCircuit size={21} />
                </div>

                <div className="form-group">
                  <label htmlFor="demo-sample">YelpChi dataset sample</label>
                  <select
                    id="demo-sample"
                    value={selectedDemoId}
                    onChange={(event) => {
                      setSelectedDemoId(event.target.value);
                      setResult(null);
                    }}
                    disabled={demoSamples.length === 0}
                  >
                    {demoSamples.map((sample) => (
                      <option key={sample.id} value={sample.id}>
                        Sample {sample.id} (test index {sample.test_index})
                      </option>
                    ))}
                  </select>
                </div>

                {selectedDemo && (
                  <p className="field-hint">
                    {selectedDemo.features.length} numeric features; dataset
                    label: class_{selectedDemo.true_label}. The model receives
                    the feature array in its saved order.
                  </p>
                )}

                {apiError && (
                  <p className="api-error" role="alert">
                    {apiError}
                  </p>
                )}

                <div className="dataset-disclaimer">
                  <AlertTriangle size={16} />
                  <span>
                    Dataset-only demonstration. These YelpChi labels and
                    predictions are not verified seller-risk classifications.
                    No text or seller form data is analyzed.
                  </span>
                </div>

                <div className="form-actions">
                  <button
                    className="primary-button"
                    onClick={analyzeDemoSample}
                    disabled={!selectedDemo || isAnalyzing}
                  >
                    {isAnalyzing ? (
                      <>
                        <span className="spinner"></span>
                        Running model...
                      </>
                    ) : (
                      <>
                        <Sparkles size={17} />
                        Predict sample
                      </>
                    )}
                  </button>
                </div>
              </div>

              <div className="analysis-side">
                {!result && !isAnalyzing && (
                  <div className="empty-analysis panel">
                    <div className="empty-icon">
                      <BrainCircuit size={38} />
                    </div>

                    <h3>Ready for a dataset demo</h3>

                    <p>
                      Choose one of the packaged YelpChi samples and run the
                      model to view its class probabilities.
                    </p>

                    <div className="analysis-steps">
                      <div>
                        <span>01</span>
                        Select a dataset sample
                      </div>

                      <div>
                        <span>02</span>
                        Apply the packaged scaler
                      </div>

                      <div>
                        <span>03</span>
                        Return class probabilities
                      </div>
                    </div>
                  </div>
                )}

                {isAnalyzing && (
                  <div className="empty-analysis panel analyzing-card">
                    <div className="loader-ring">
                      <BrainCircuit size={34} />
                    </div>

                    <h3>Running model...</h3>

                    <p>
                      Applying the packaged scaler and classifier to this
                      dataset sample.
                    </p>

                    <div className="loading-lines">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                )}

                {result && (
                  <div className="dataset-result panel">
                    <div className="result-header">
                      <div>
                        <p className="eyebrow">DATASET MODEL OUTPUT</p>
                        <h3>Sample {result.sample.id}</h3>
                      </div>
                    </div>

                    <div className="result-class">
                      <span>Predicted class</span>
                      <strong>{result.predicted_class}</strong>
                    </div>

                    <div className="probability-list">
                      {Object.entries(result.probabilities).map(
                        ([label, probability]) => (
                          <div className="probability-row" key={label}>
                            <span>{label}</span>
                            <strong>{(probability * 100).toFixed(2)}%</strong>
                          </div>
                        )
                      )}
                    </div>

                    <div className="demo-warning">
                      <AlertTriangle size={15} />
                      {result.scope}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        {activePage === "Analytics" && (
          <section className="page">
            <div className="page-intro">
              <div>
                <p className="eyebrow">INSIGHTS</p>
                <h2>Detection analytics</h2>
                <p>
                  Illustrative charts only; these figures are not model
                  predictions or seller analyses.
                </p>
              </div>

              <span className="demo-label">ILLUSTRATIVE DATA</span>
            </div>

            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon blue">
                  <Activity size={21} />
                </div>

                <span className="stat-label">Average risk score</span>
                <strong className="stat-number">—</strong>
                <span className="stat-description">No seller assessment</span>
              </div>

              <div className="stat-card">
                <div className="stat-icon red">
                  <ShieldAlert size={21} />
                </div>

                <span className="stat-label">High risk rate</span>
                <strong className="stat-number">—</strong>
                <span className="stat-description">No seller assessment</span>
              </div>

              <div className="stat-card">
                <div className="stat-icon green">
                  <CheckCircle2 size={21} />
                </div>

                <span className="stat-label">Safe rate</span>
                <strong className="stat-number">—</strong>
                <span className="stat-description">No seller assessment</span>
              </div>

              <div className="stat-card">
                <div className="stat-icon purple">
                  <Zap size={21} />
                </div>

                <span className="stat-label">Model inputs</span>
                <strong className="stat-number">32</strong>
                <span className="stat-description">Numerical features</span>
              </div>
            </div>

            <div className="analytics-grid">
              <div className="panel">
                <div className="panel-header">
                  <div>
                    <p className="eyebrow">RISK TREND</p>
                    <h3>Illustrative trend only</h3>
                  </div>
                </div>

                <ResponsiveContainer width="100%" height={320}>
                  <LineChart data={trendData}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                    />

                    <XAxis dataKey="day" />

                    <YAxis />

                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="risk"
                      stroke="#8da8e8"
                      strokeWidth={3}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <div>
                    <p className="eyebrow">MODEL SCOPE</p>
                    <h3>Verified facts</h3>
                  </div>
                </div>

                <div className="factor-list">
                  <div className="factor">
                    <div>
                      <span>Training dataset</span>
                      <small>YelpChi</small>
                    </div>

                    <strong>Known</strong>
                  </div>

                  <div className="factor">
                    <div>
                      <span>Input width</span>
                      <small>Numerical features</small>
                    </div>

                    <strong>32</strong>
                  </div>

                  <div className="factor">
                    <div>
                      <span>Class meanings</span>
                      <small>Not verified</small>
                    </div>

                    <strong>—</strong>
                  </div>

                  <div className="factor">
                    <div>
                      <span>Seller mapping</span>
                      <small>Not documented</small>
                    </div>

                    <strong>—</strong>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {activePage === "History" && (
          <section className="page">
            <div className="page-intro history-intro">
              <div>
                <p className="eyebrow">RECORDS</p>
                <h2>Seller history</h2>
                <p>
                  No seller-specific analyses are recorded by the dataset demo.
                </p>
              </div>

              <button className="export-button" onClick={exportHistory}>
                <Download size={17} />
                Export CSV
              </button>
            </div>

            <div className="history-summary">
              <div className="history-summary-card">
                <div className="stat-icon blue">
                  <FileText size={20} />
                </div>

                <div>
                  <span>Total records</span>
                  <strong>{history.length}</strong>
                </div>
              </div>

              <div className="history-summary-card">
                <div className="stat-icon red">
                  <ShieldAlert size={20} />
                </div>

                <div>
                  <span>Suspicious</span>
                  <strong>{suspiciousCount}</strong>
                </div>
              </div>

              <div className="history-summary-card">
                <div className="stat-icon green">
                  <ShieldCheck size={20} />
                </div>

                <div>
                  <span>Safe</span>
                  <strong>{safeCount}</strong>
                </div>
              </div>
            </div>

            <div className="panel history-panel">
              <div className="history-toolbar">
                <div>
                  <p className="eyebrow">SEARCH & FILTER</p>
                  <h3>Find a detection</h3>
                </div>

                <div className="filter-count">
                  {filteredHistory.length} of {history.length} records
                </div>
              </div>

              <div className="history-filters">
                <div className="search-box">
                  <Search size={18} />

                  <input
                    type="text"
                    placeholder="Search seller ID or category..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />

                  {searchTerm && (
                    <button
                      className="clear-search"
                      onClick={() => setSearchTerm("")}
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>

                <div className="filter-select">
                  <Filter size={16} />

                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    <option value="All">All Status</option>
                    <option value="Safe">Safe</option>
                    <option value="Suspicious">Suspicious</option>
                  </select>
                </div>

                <div className="filter-select">
                  <select
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                  >
                    <option value="All">All Categories</option>
                    <option value="Electronics">Electronics</option>
                    <option value="Fashion">Fashion</option>
                    <option value="Beauty">Beauty</option>
                    <option value="Home & Kitchen">Home & Kitchen</option>
                    <option value="Sports">Sports</option>
                    <option value="Books">Books</option>
                  </select>
                </div>

                <button className="clear-filters" onClick={resetFilters}>
                  <RefreshCcw size={16} />
                  Clear
                </button>
              </div>

              {filteredHistory.length > 0 ? (
                <div className="table-container">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>Seller</th>
                        <th>Category</th>
                        <th>Risk Score</th>
                        <th>Status</th>
                        <th>Reviews</th>
                        <th>Date</th>
                        <th></th>
                      </tr>
                    </thead>

                    <tbody>
                      {filteredHistory.map((record) => (
                        <tr key={`${record.id}-${record.date}`}>
                          <td>
                            <div className="seller-cell">
                              <div className="seller-avatar">
                                {record.id.slice(-2)}
                              </div>

                              <div>
                                <strong>{record.id}</strong>
                                <span>Seller profile</span>
                              </div>
                            </div>
                          </td>

                          <td>
                            <span className="category-pill">
                              {record.category}
                            </span>
                          </td>

                          <td>
                            <div className="score-cell">
                              <strong>{record.score}</strong>

                              <div className="mini-progress">
                                <span
                                  style={{
                                    width: `${record.score}%`,
                                  }}
                                ></span>
                              </div>
                            </div>
                          </td>

                          <td>
                            <span
                              className={`status-badge ${
                                record.status === "Suspicious"
                                  ? "status-danger"
                                  : "status-safe"
                              }`}
                            >
                              {record.status === "Suspicious" ? (
                                <ShieldAlert size={14} />
                              ) : (
                                <ShieldCheck size={14} />
                              )}

                              {record.status}
                            </span>
                          </td>

                          <td>{record.reviews}</td>

                          <td>{record.date}</td>

                          <td>
                            <button
                              className="view-button"
                              title="View record"
                              onClick={() =>
                                alert(
                                  `Seller: ${record.id}\nRisk Score: ${record.score}\nStatus: ${record.status}`
                                )
                              }
                            >
                              <Eye size={17} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="no-results">
                  <div className="no-results-icon">
                    <Search size={28} />
                  </div>

                  <h3>No records found</h3>

                  <p>
                    No detection records match your current search and
                    filters.
                  </p>

                  <button
                    className="secondary-button"
                    onClick={resetFilters}
                  >
                    <RefreshCcw size={16} />
                    Reset Filters
                  </button>
                </div>
              )}
            </div>
          </section>
        )}

        {activePage === "Model" && (
          <section className="page">
            <div className="page-intro">
              <div>
                <p className="eyebrow">DATASET CLASSIFIER</p>
                <h2>Model intelligence</h2>
                <p>
                  Verified details of the packaged model and its limits.
                </p>
              </div>

              <div className="engine-status">
                <span></span>
                {apiStatus === "online" ? "API Online" : "API Unavailable"}
              </div>
            </div>

            <div className="model-hero panel">
              <div className="model-logo">
                <BrainCircuit size={42} />
              </div>

              <div>
                <p className="eyebrow">PACKAGED PYTORCH MODEL</p>
                <h2>32-feature neural network</h2>

                <p>
                  Linear(32,128) → ReLU → Dropout(0.3) → Linear(128,64) →
                  ReLU → Dropout(0.3) → Linear(64,32) → ReLU → Dropout(0.2) →
                  Linear(32,2). Trained on YelpChi; not verified on
                  e-commerce sellers.
                </p>
              </div>

              <div className="model-score">
                <span>INPUT WIDTH</span>
                <strong>32</strong>
              </div>
            </div>

            <div className="pipeline">
              <div className="pipeline-line"></div>

              <div className="pipeline-step">
                <div className="pipeline-number">01</div>

                <div className="pipeline-card">
                  <FileText size={22} />
                  <h3>Input Data</h3>
                  <p>32 numerical dataset features</p>
                </div>
              </div>

              <div className="pipeline-step">
                <div className="pipeline-number">02</div>

                <div className="pipeline-card">
                  <BrainCircuit size={22} />
                  <h3>StandardScaler</h3>
                  <p>Previously fitted feature scaling</p>
                </div>
              </div>

              <div className="pipeline-step">
                <div className="pipeline-number">03</div>

                <div className="pipeline-card">
                  <Activity size={22} />
                  <h3>Deep Learning</h3>
                  <p>Neural network classification</p>
                </div>
              </div>

              <div className="pipeline-step">
                <div className="pipeline-number">04</div>

                <div className="pipeline-card">
                  <ShieldCheck size={22} />
                  <h3>Prediction</h3>
                  <p>Uninterpreted class_0 or class_1 output</p>
                </div>
              </div>
            </div>

            <div className="model-info-grid">
              <div className="panel">
                <p className="eyebrow">CAPABILITIES</p>
                <h3>What is verified</h3>

                <div className="capability-list">
                  <div>
                    <CheckCircle2 size={18} />
                    32 numerical inputs
                  </div>

                  <div>
                    <CheckCircle2 size={18} />
                    Packaged feature scaler
                  </div>

                  <div>
                    <CheckCircle2 size={18} />
                    YelpChi demo samples
                  </div>

                  <div>
                    <AlertTriangle size={18} />
                    No seller-field mapping
                  </div>
                </div>
              </div>

              <div className="panel">
                <p className="eyebrow">SYSTEM STATUS</p>
                <h3>Current deployment</h3>

                <div className="system-status-list">
                  <div>
                    <span>Frontend</span>
                    <strong className="online">Online</strong>
                  </div>

                  <div>
                    <span>Detection engine</span>
                    <strong className={apiStatus === "online" ? "online" : "pending"}>
                      {apiStatus === "online" ? "Ready" : "Unavailable"}
                    </strong>
                  </div>

                  <div>
                    <span>ML backend</span>
                    <strong className="online">YelpChi demo</strong>
                  </div>

                  <div>
                    <span>Model API</span>
                    <strong className={apiStatus === "online" ? "online" : "pending"}>
                      {apiStatus === "online" ? "Connected" : "Not connected"}
                    </strong>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;