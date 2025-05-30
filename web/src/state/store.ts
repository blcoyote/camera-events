import { configureStore } from "@reduxjs/toolkit";
// Or from '@reduxjs/toolkit/query/react'
import { setupListeners } from "@reduxjs/toolkit/query";
import { cameraApi } from "../services/camera-api";
import authSlice from "./auth-slice";

export const store = configureStore({
	reducer: {
		// Add the generated reducer as a specific top-level slice
		[cameraApi.reducerPath]: cameraApi.reducer,
		auth: authSlice,
	},
	// Adding the api middleware enables caching, invalidation, polling,
	// and other useful features of `rtk-query`.
	middleware: (getDefaultMiddleware) =>
		getDefaultMiddleware().concat(cameraApi.middleware),
});

// optional, but required for refetchOnFocus/refetchOnReconnect behaviors
// see `setupListeners` docs - takes an optional callback as the 2nd arg for customization
setupListeners(store.dispatch);

// export rootstate for reducer hooks
export type RootState = ReturnType<typeof store.getState>;
// export AppDispatch for dispatching actions
export type AppDispatch = typeof store.dispatch;
