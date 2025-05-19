import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { baseUrl } from "../config/service";
import type { AppConfig } from "../models/app-config.model";
import type { CameraEvent } from "../models/camera-event.model";

export const cameraApi = createApi({
	reducerPath: "cameraApi",
	baseQuery: fetchBaseQuery({
		baseUrl: `${baseUrl()}/api`,

		prepareHeaders: (headers) => {
			headers.set("Content-Type", 'application/json;charset=UTF-8"');
			headers.set("Access-Control-Allow-Origin", "*");
			headers.set("Access-Control-Allow-Credentials", "true");
			headers.set("x-token", sessionStorage.getItem("fbtoken") ?? "");
			return headers;
		},
	}),
	refetchOnFocus: true,
	refetchOnReconnect: true,
	refetchOnMountOrArgChange: true,
	tagTypes: ["CameraEvents"],
	endpoints: (builder) => ({
		getCameraEvents: builder.query<CameraEvent[], number>({
			query: (queryArg) => ({
				method: "GET",
				url: "/v2/events/",
				params: { limit: queryArg },
			}),
			providesTags: ["CameraEvents"],
		}),
		getCameraEventDetails: builder.query<CameraEvent, string>({
			query: (id) => ({ method: "GET", url: `/v2/events/${id}` }),
			providesTags: ["CameraEvents"],
		}),
		getApplicationConfiguration: builder.query<AppConfig, void>({
			query: () => ({
				method: "GET",
				url: "/v1/application-configuration",
			}),
		}),
	}),
});

export const {
	useGetCameraEventsQuery,
	useGetCameraEventDetailsQuery,
	useGetApplicationConfigurationQuery,
} = cameraApi;
