export const formatTime = (time) => {
  const minutes = Math.floor(time / 60);
  const seconds = (time % 60).toFixed(3).padStart(6, '0');
  return `${minutes}:${seconds}`;
};

export const saveToServer = (fileName, data, toastMessage, setToast) => {
  const SongsFolder = '/songs/';

  fetch(SongsFolder + "save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fileName: fileName, data: data })
    })
    .then(res => res.ok ? setToast(toastMessage) : setToast("Failed to save."))
    .catch(err => {
    console.error("Save error:", err);
    setToast("Save failed.");
    });
};