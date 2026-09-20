function AnalysisStatus({
    status,
}) {

    if (!status) {
        return null;
    }

    return (
        <div className="analysis-status">

            <div>

                <span className="label">
                    Session
                </span>

                <strong>
                    #{status.session_id}
                </strong>

            </div>

            <div>

                <span className="label">
                    Source
                </span>

                <strong>
                    {status.source_type}
                </strong>

            </div>

            <div>

                <span className="label">
                    Frames
                </span>

                <strong>
                    {status.total_frames ??
                        "—"}
                </strong>

            </div>

            <div>

                <span className="label">
                    Resolution
                </span>

                <strong>
                    {status.width &&
                    status.height
                        ? `${status.width} × ${status.height}`
                        : "—"}
                </strong>

            </div>

            <div>

                <span className="label">
                    Status
                </span>

                <strong
                    className={`analysis-state ${
                        (
                            status.status ||
                            ""
                        ).toLowerCase()
                    }`}
                >
                    {status.status}
                </strong>

            </div>

        </div>
    );
}

export default AnalysisStatus;