import { TrackReferenceOrPlaceholder, useLocalParticipant } from "@livekit/components-react";
import { Track } from "livekit-client";
import { useMemo } from "react";

/**
 * useLocalMicTrack is a custom hook that provides a reference to the local participant's microphone track.
 *
 * It retrieves the local participant and their microphone track from the LiveKit context
 * and memoizes the track reference object.
 *
 * @returns {TrackReferenceOrPlaceholder} A reference object containing the participant, source, and publication.
 */
export default function useLocalMicTrack() {
  const { microphoneTrack, localParticipant } = useLocalParticipant();

  const micTrackRef: TrackReferenceOrPlaceholder = useMemo(() => {
    return {
      participant: localParticipant,
      source: Track.Source.Microphone,
      publication: microphoneTrack,
    };
  }, [localParticipant, microphoneTrack]);

  return micTrackRef;
}
