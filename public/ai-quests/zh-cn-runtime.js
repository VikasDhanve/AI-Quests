if(/\/intl\/zh_cn(?:\/|$)/.test(location.pathname)){
const show=(video)=>{for(const track of video.querySelectorAll('track')){if(!['subtitles','captions'].includes(track.kind))continue;track.srclang='zh-CN';track.label='简体中文';track.default=true;track.track.mode='showing';}};
document.addEventListener('loadedmetadata',e=>{if(e.target instanceof HTMLVideoElement)show(e.target);},true);
document.addEventListener('load',e=>{if(e.target instanceof HTMLTrackElement&&e.target.parentElement instanceof HTMLVideoElement)show(e.target.parentElement);},true);
}
