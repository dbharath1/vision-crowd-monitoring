function CrowdStats({
    summary,
}) {

    const latest =
        summary?.latest;

    const formatNumber = (
        value,
        decimals = 2
    ) => {

        if (
            value === null ||
            value === undefined
        ) {
            return "—";
        }

        return Number(value).toFixed(
            decimals
        );
    };


    const stats = [

        {
            label: "Persons",
            value:
                latest?.person_count ??
                "—",
        },

        {
            label: "Density",
            value: latest
                ? formatNumber(
                      latest.density,
                      6
                  )
                : "—",
        },

        {
            label: "Moving",
            value:
                latest?.moving_persons ??
                "—",
        },

        {
            label: "Stationary",
            value:
                latest
                    ?.stationary_persons ??
                "—",
        },

        {
            label: "Groups",
            value:
                latest?.group_count ??
                "—",
        },

        {
            label: "Avg. Speed",
            value:
                latest?.average_speed !=
                null
                    ? `${formatNumber(
                          latest.average_speed
                      )} px/s`
                    : "—",
        },

    ];


    return (
        <div className="stats-grid">

            {stats.map((stat) => (

                <div
                    className="stat-card"
                    key={stat.label}
                >

                    <span>
                        {stat.label}
                    </span>

                    <strong>
                        {stat.value}
                    </strong>

                </div>

            ))}

        </div>
    );
}

export default CrowdStats;