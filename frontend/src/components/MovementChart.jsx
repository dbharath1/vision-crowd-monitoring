import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
} from "recharts";


function MovementChart({
    frames,
}) {

    if (!frames?.length) {

        return (
            <div className="chart-panel">

                <h2>
                    Movement
                </h2>

                <div className="empty-state">
                    No movement data available.
                </div>

            </div>
        );
    }


    const data =
        frames.map((frame) => ({
            frame:
                frame.frame_id,

            moving:
                frame.moving_persons ??
                0,

            stationary:
                frame.stationary_persons ??
                0,
        }));


    return (
        <div className="chart-panel">

            <div className="panel-heading">

                <div>

                    <h2>
                        Crowd Movement
                    </h2>

                    <p>
                        Moving versus
                        stationary persons
                    </p>

                </div>

            </div>

            <ResponsiveContainer
                width="100%"
                height={300}
            >

                <LineChart
                    data={data}
                >

                    <CartesianGrid
                        strokeDasharray="3 3"
                    />

                    <XAxis
                        dataKey="frame"
                    />

                    <YAxis />

                    <Tooltip />

                    <Legend />

                    <Line
                        type="monotone"
                        dataKey="moving"
                        strokeWidth={2}
                        dot={false}
                    />

                    <Line
                        type="monotone"
                        dataKey="stationary"
                        strokeWidth={2}
                        dot={false}
                    />

                </LineChart>

            </ResponsiveContainer>

        </div>
    );
}

export default MovementChart;