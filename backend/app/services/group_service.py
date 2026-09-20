from sklearn.cluster import DBSCAN
import numpy as np

from app.core.config import settings


class CrowdGroupService:
    """
    Detects spatial crowd groups using DBSCAN.

    DBSCAN groups people according to their spatial
    proximity without requiring the number of groups
    to be known beforehand.
    """

    def __init__(
        self,
        eps: float | None = None,
        min_samples: int | None = None,
    ):

        self.eps = (
            eps
            if eps is not None
            else settings.dbscan_eps
        )

        self.min_samples = (
            min_samples
            if min_samples is not None
            else settings.dbscan_min_samples
        )

        if self.eps <= 0:
            raise ValueError(
                "DBSCAN eps must be greater than zero."
            )

        if self.min_samples < 1:
            raise ValueError(
                "DBSCAN min_samples must be at least 1."
            )

    def cluster(
        self,
        tracks: list[dict],
    ) -> dict:
        """
        Cluster tracked people based on their
        center positions.
        """

        if not tracks:
            return {
                "groups": [],
                "noise_track_ids": [],
                "track_assignments": {},
            }

        # Extract person center coordinates.
        points = np.array(
            [
                track["center"]
                for track in tracks
            ],
            dtype=float,
        )

        # Apply DBSCAN.
        clustering = DBSCAN(
            eps=self.eps,
            min_samples=self.min_samples,
        ).fit(points)

        labels = clustering.labels_

        track_assignments = {}
        groups = {}

        for track, label in zip(
            tracks,
            labels,
        ):

            track_id = int(
                track["track_id"]
            )

            label = int(label)

            track_assignments[
                track_id
            ] = label

            # DBSCAN label -1 means noise.
            if label == -1:
                continue

            if label not in groups:
                groups[label] = []

            groups[label].append(track)

        group_results = []

        for group_id, group_tracks in groups.items():

            centers = np.array(
                [
                    track["center"]
                    for track in group_tracks
                ],
                dtype=float,
            )

            # Group centroid.
            centroid_x = float(
                np.mean(centers[:, 0])
            )

            centroid_y = float(
                np.mean(centers[:, 1])
            )

            x_values = centers[:, 0]
            y_values = centers[:, 1]

            # Spatial bounding box of the group.
            bounding_box = [
                float(np.min(x_values)),
                float(np.min(y_values)),
                float(np.max(x_values)),
                float(np.max(y_values)),
            ]

            group_results.append(
                {
                    "group_id": int(group_id),

                    "member_count": len(
                        group_tracks
                    ),

                    "track_ids": [
                        int(track["track_id"])
                        for track in group_tracks
                    ],

                    "centroid": [
                        centroid_x,
                        centroid_y,
                    ],

                    "bounding_box": bounding_box,
                }
            )

        # People not assigned to a group.
        noise_track_ids = [
            int(track["track_id"])
            for track, label in zip(
                tracks,
                labels,
            )
            if int(label) == -1
        ]

        return {
            "groups": group_results,

            "noise_track_ids": (
                noise_track_ids
            ),

            "track_assignments": (
                track_assignments
            ),
        }

    def calculate_group_movement(
        self,
        groups: list[dict],
        movement_results: dict[int, dict],
    ) -> list[dict]:
        """
        Add movement statistics to each
        detected crowd group.
        """

        enriched_groups = []

        for group in groups:

            speeds = []
            displacements = []
            directions = []

            for track_id in group[
                "track_ids"
            ]:

                movement = movement_results.get(
                    track_id
                )

                if not movement:
                    continue

                if movement["speed"] is not None:
                    speeds.append(
                        movement["speed"]
                    )

                displacements.append(
                    movement["displacement"]
                )

                directions.append(
                    movement["direction"]
                )

            enriched_group = dict(group)

            # Average group speed.
            enriched_group[
                "average_speed"
            ] = (
                sum(speeds) / len(speeds)
                if speeds
                else None
            )

            # Average member displacement.
            enriched_group[
                "average_displacement"
            ] = (
                sum(displacements)
                / len(displacements)
                if displacements
                else 0.0
            )

            # Directions of members.
            enriched_group[
                "directions"
            ] = directions

            enriched_groups.append(
                enriched_group
            )

        return enriched_groups