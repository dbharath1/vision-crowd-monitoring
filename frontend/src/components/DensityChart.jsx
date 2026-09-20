import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
} from "recharts";


function DensityChart({
    frames,
}) {

    if (!frames?.length) {

        return (
            <div className="chart-panel">

                <h2>
                    Density
                </h2>

                <div className="empty-state">
                    No frame data available.
                </div>

            </div>
        );
    }


    const data =
        frames.map((frame) => ({
            frame:
                frame.frame_id,
            density:
                frame.density ?? 0,
        }));


    return (
        <div className="chart-panel">

            <div className="panel-heading">

                <div>
                    <h2>
                        Crowd Density
                    </h2>

                    <p>
                        Density calculated
                        for each processed
                        frame
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

                    <Line
                        type="monotone"
                        dataKey="density"
                        strokeWidth={2}
                        dot={false}
                    />

                </LineChart>

            </ResponsiveContainer>

        </div>
    );
}

export default DensityChart;