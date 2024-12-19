import { isRouteErrorResponse, useRouteError } from "react-router-dom";
import { EventListCard } from "../components/event-list-card";
import { EventListCardLoader } from "../components/event-list-card/event-list-card-loader";
import { useGetCameraEventsQuery } from "../services/camera-api";
import useSettings from "../hooks/use-settings";
import { useIdToken } from "react-firebase-hooks/auth";
import { auth } from "../config/firebase";
import PullToRefresh from "pulltorefreshjs";
import { useEffect } from "react";

export const Component = () => {
  const { eventLimit } = useSettings();
  const [user] = useIdToken(auth);
  const token = user?.getIdToken();
  const { data, isLoading, isFetching, refetch } = useGetCameraEventsQuery(
    eventLimit,
    {
      skip: !token,
    }
  );

  const loading = isFetching || isLoading;

  useEffect(() => {
    PullToRefresh.init({
      mainElement: "body",
      onRefresh: () => {
        refetch();
      },
    });
    return PullToRefresh.destroyAll();
  }, []);

  return (
    <div className="grid content-center pt-5 lg:grid-cols-2 gap-4 w-max-dvw">
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
