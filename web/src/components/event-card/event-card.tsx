import type { CameraEvent } from "../../models/camera-event.model";
import { motion } from "motion/react";
import dayjs from "dayjs";
import { HiFilm, HiPhoto } from "react-icons/hi2";
import { CameraNames } from "../../config/enum-camera-names";
import {
	useEventClipDownload,
	useEventSnapshotDownload,
} from "../../hooks/use-event";
import { toast } from "react-toastify";
import { useEffect } from "react";

interface EventCardProps {
	event?: CameraEvent;
	isError: boolean;
	snapshotData?: string;
}

export const EventCard = (props: EventCardProps) => {
	const { event, isError, snapshotData } = props;
	const image = snapshotData && `data:image/jpeg;base64,${snapshotData}`;
	const {
		download: downloadSnapshot,
		loading: snapshotLoading,
		isSuccess: isSnapShotSuccess,
		error: snapShotError,
	} = useEventSnapshotDownload(event?.id);
	const {
		download: downloadClip,
		loading: clipLoading,
		error: clipError,
		isSuccess: isClipSuccess,
	} = useEventClipDownload(event?.id);

	useEffect(() => {
		if (isSnapShotSuccess) {
			toast.success("Snapshot downloaded successfully");
		}
		if (snapShotError) {
			toast.error("Failed to download snapshot");
		}
	}, [isSnapShotSuccess, snapShotError]);
	useEffect(() => {
		if (isClipSuccess) {
			toast.success("Clip downloaded successfully");
		}
		if (clipError) {
			toast.error("Failed to download clip");
		}
	}, [isClipSuccess, clipError]);

	if (isError) {
		return <div>Error...</div>;
	}

	return (
		<div className="card-normal bg-base-100 max-w-xl max-h-dvh rounded-box shadow-xl ">
			<figure>
				<img src={image} alt="survellance" className="rounded-t-box" />
			</figure>
			<div className="card-body relative">
				<div className="badge absolute top-2 right-2 badge-outline">
					{CameraNames[event?.camera as keyof typeof CameraNames] ?? "Unknown"}
				</div>
				<h2 className="card-title">
					{event &&
						dayjs.unix(event?.start_time).format("DD MMM. YYYY HH:mm:ss")}
				</h2>
				<p>{`Label: ${event?.label}`}</p>
				<p>{`Probability: ${event && (event?.data.score * 100).toFixed(2)}%`}</p>
				<p>{`EventId: ${event?.id}`}</p>
				<div className="divider" />
				<div className="flex justify-evenly ">
					<motion.button
						initial={{ opacity: 0, scale: 0.5 }}
						animate={{ opacity: 1, scale: 1 }}
						transition={{ duration: 0.5 }}
						title="Download Snapshot"
						onClick={() => downloadSnapshot()}
						disabled={snapshotLoading}
						className="relative"
					>
						{snapshotLoading ? (
							<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary" />
						) : (
							<HiPhoto size={32} className="cursor-pointer" />
						)}
					</motion.button>
					<motion.button
						initial={{ opacity: 0, scale: 0.5 }}
						animate={{ opacity: 1, scale: 1 }}
						transition={{ duration: 0.5 }}
						title="Download Clip"
						onClick={() => downloadClip()}
						disabled={clipLoading}
						className="relative"
					>
						{clipLoading ? (
							<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary" />
						) : (
							<HiFilm size={32} className="cursor-pointer" />
						)}
					</motion.button>
				</div>
			</div>
		</div>
	);
};
