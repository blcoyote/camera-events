import { type FirebaseOptions, initializeApp } from "firebase/app";
import { GoogleAuthProvider, getAuth } from "firebase/auth";
import {
  type MessagePayload,
  getToken,
  onMessage,
  getMessaging,
} from "firebase/messaging";
import { baseUrl } from "./service";

const fetchAppConfig = async () => {
  try {
    const response = await fetch(
      `${baseUrl()}/api/v1/application-configuration`
    );
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    const data = await response.json();
    return data as FirebaseOptions;
  } catch (error) {
    console.error("Failed to fetch application configuration:", error);
    throw error;
  }
};

export const app = initializeApp(await fetchAppConfig());

export const auth = getAuth(app);

export const googleProvider = new GoogleAuthProvider();

export const messaging = getMessaging(app);

export const getMessageToken = async (
  setTokenFound: React.Dispatch<React.SetStateAction<string | undefined>>,
  messagingKey: string
) => {
  try {
    const currentToken = await getToken(messaging, {
      vapidKey: messagingKey,
    });
    if (currentToken) {
      //"current fcm token for client: ", currentToken
      setTokenFound(currentToken);
    } else {
      //'No registration token available. Request permission to generate one.'
      setTokenFound(undefined);
    }
  } catch (err) {
    console.log("An error occurred while retrieving token. ", err);
  }
};

export const onMessageListener = (): Promise<MessagePayload> =>
  new Promise((resolve) => {
    onMessage(messaging, (payload) => {
      resolve(payload);
    });
  });
