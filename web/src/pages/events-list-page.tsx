import { isRouteErrorResponse, useRouteError } from "react-router-dom";
import { EventListCard } from "../components/event-list-card";
import { EventListCardLoader } from "../components/event-list-card/event-list-card-loader";
import { useGetCameraEventsQuery } from "../services/camera-api";
import useSettings from "../hooks/use-settings";
import { useIdToken } from "react-firebase-hooks/auth";
import { auth } from "../config/firebase";
import PullToRefresh from "pulltorefreshjs";
import { useEffect } from "react";
import ReactDOMServer from "react-dom/server";

export const Component = () => {
	const { eventLimit } = useSettings();
	const [user] = useIdToken(auth);
	const token = user?.getIdToken();
	const { data, isLoading, isFetching, refetch } = useGetCameraEventsQuery(
		eventLimit,
		{
			skip: !token,
		},
	);

	useEffect(() => {
		const handleVisibilityChange = () => {
			if (document.visibilityState === "visible") {
				refetch();
			}
		};

		document.addEventListener("visibilitychange", handleVisibilityChange);

		return () => {
			document.removeEventListener("visibilitychange", handleVisibilityChange);
		};
	}, [refetch]);

	const loading = isFetching || isLoading;

	useEffect(() => {
		PullToRefresh.init({
			instructionsPullToRefresh: ReactDOMServer.renderToString(
				<div className="text-primary">Træk for at genopfriske</div>,
			),
			instructionsReleaseToRefresh: ReactDOMServer.renderToString(
				<div className="text-primary">Slip for at genopfriske</div>,
			),
			iconArrow: ReactDOMServer.renderToString(
				<div className="text-primary">&#8675;</div>,
			),
			iconRefreshing: ReactDOMServer.renderToString(
				<div className="text-primary">&hellip;</div>,
			),
			instructionsRefreshing: ReactDOMServer.renderToString(
				<div className="text-primary">Genopfrisker...</div>,
			),
			mainElement: "body",
		});
	}, []);

	return (
		<div className="grid content-center pt-5 md:grid-cols-2 xl:grid-cols-3 gap-4 w-max-dvw">
			{loading && [1, 2, 3].map((key) => <EventListCardLoader key={key} />)}
			{!loading &&
				data?.map((event) => (
					<EventListCard key={event.id} {...event} isLoading={loading} />
				))}
		</div>
	);
};

Component.displayName = "EventListLazyRoute";

export function ErrorBoundary() {
	const error = useRouteError();
	return isRouteErrorResponse(error) ? (
		<h1>
			{error.status} {error.statusText}
		</h1>
	) : (
		<h1>{error?.toString()}</h1>
	);
}

ErrorBoundary.displayName = "EventListErrorBoundary";
