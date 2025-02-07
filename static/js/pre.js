const video = document.getElementById("myVideo");
function playVideo() {
  video.play();
}
function pauseVideo() {
  video.pause();
}
// Rewind the video by 10 seconds
function rewindVideo() {
  video.currentTime -= 5;
}
function fastForwardVideo() {
  video.currentTime += 5;
}