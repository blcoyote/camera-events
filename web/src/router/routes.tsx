import { createBrowserRouter } from "react-router-dom";
import { PageLoader } from "../pages/page-loader";
import { Layout } from "../layout/layout";

export const router = createBrowserRouter([
	{
		element: <Layout />,
		loader: PageLoader,
		children: [
			{ path: "*", lazy: () => import("../pages/not-found-page") },
			{ path: "/", lazy: () => import("../pages/events-list-page") },
			{
				path: "events",
				lazy: () => import("../pages/events-list-page"),
			},
			{
				path: "events/:id",
				lazy: () => import("../pages/event-details-page"),
			},
			{
				path: "event/:id",
				lazy: () => import("../pages/event-details-page"),
			},
			{
				path: "eventnotification/:id",
				lazy: () => import("../pages/event-details-page"),
			},
			{ path: "about", lazy: () => import("../pages/about-page") },
			{ path: "settings", lazy: () => import("../pages/settings-page") },
			{ path: "test", lazy: () => import("../pages/test-page") },
		],
	},
]);
