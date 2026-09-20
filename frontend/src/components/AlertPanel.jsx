function AlertPanel({
    alerts,
}) {

    return (
        <div className="information-card">

            <div className="panel-heading">

                <div>

                    <h2>
                        Alerts
                    </h2>

                    <p>
                        Alerts generated from
                        computed conditions
                    </p>

                </div>

                <span className="alert-count">
                    {alerts?.length ?? 0}
                </span>

            </div>


            {!alerts?.length ? (

                <div className="empty-state">
                    No alerts generated.
                </div>

            ) : (

                <div className="alert-list">

                    {alerts
                        .slice()
                        .reverse()
                        .map((alert) => (

                            <div
                                className="alert-item"
                                key={alert.id}
                            >

                                <div className="alert-main">

                                    <strong>
                                        {
                                            alert.alert_type
                                        }
                                    </strong>

                                    <span>
                                        {
                                            alert.message
                                        }
                                    </span>

                                </div>

                                <div className="alert-meta">

                                    Frame{" "}
                                    {
                                        alert.frame_id
                                    }

                                </div>

                            </div>

                        ))}

                </div>

            )}

        </div>
    );
}

export default AlertPanel;