function Header({ status }) {
    return (
        <header className="app-header">

            <div className="brand">

                <div className="brand-icon">
                    C
                </div>

                <div>
                    <h1>
                        CrowdWatch
                    </h1>

                    <p>
                        Vision-Based Crowd
                        Congestion Monitoring
                    </p>
                </div>

            </div>

            <div className="header-status">

                <span
                    className={`status-dot ${
                        status === "PROCESSING"
                            ? "processing"
                            : status ===
                              "COMPLETED"
                            ? "completed"
                            : status ===
                              "FAILED"
                            ? "failed"
                            : ""
                    }`}
                />

                <span>
                    {status ||
                        "NO ANALYSIS"}
                </span>

            </div>

        </header>
    );
}

export default Header;