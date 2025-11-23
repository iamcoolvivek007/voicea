import { useTrackTranscription, useVoiceAssistant } from "@livekit/components-react";
import { useMemo } from "react";
import useLocalMicTrack from "./useLocalMicTrack";

/**
 * useCombinedTranscriptions is a custom hook that aggregates transcriptions from both the agent and the user.
 *
 * It retrieves agent transcriptions from the `useVoiceAssistant` hook and user transcriptions
 * from the `useTrackTranscription` hook (using the local microphone track). It then combines
 * and sorts them by reception time to provide a chronological conversation history.
 *
 * @returns {Array<object>} An array of transcription segments, each with an added `role` property ("assistant" or "user").
 */
export default function useCombinedTranscriptions() {
  const { agentTranscriptions } = useVoiceAssistant();

  const micTrackRef = useLocalMicTrack();
  const { segments: userTranscriptions } = useTrackTranscription(micTrackRef);

  const combinedTranscriptions = useMemo(() => {
    return [
      ...agentTranscriptions.map((val) => {
        return { ...val, role: "assistant" };
      }),
      ...userTranscriptions.map((val) => {
        return { ...val, role: "user" };
      }),
    ].sort((a, b) => a.firstReceivedTime - b.firstReceivedTime);
  }, [agentTranscriptions, userTranscriptions]);

  return combinedTranscriptions;
}
