import os from 'os';

let requestCount = 0;
let errorCount = 0;
let feedServedCount = 0;
let profileViewCount = 0;
let uploadFailedCount = 0;
let rateLimited429Count = 0;
let unauthorized401Count = 0;
let likeAddedCount = 0;
let likeRemovedCount = 0;

// Web Vitals (simple aggregate)
type VitalName = 'CLS' | 'LCP' | 'FID' | 'INP';
const vitalSum: Record<VitalName, number> = { CLS: 0, LCP: 0, FID: 0, INP: 0 };
const vitalCount: Record<VitalName, number> = { CLS: 0, LCP: 0, FID: 0, INP: 0 };

// Frontend timings
let feedLoadMsSum = 0;
let feedLoadMsCount = 0;

export function incRequest() {
  requestCount += 1;
}
export function incError() {
  errorCount += 1;
}

export function incFeedServed() {
  feedServedCount += 1;
}

export function incProfileView() {
  profileViewCount += 1;
}

export function incUploadFailed() {
  uploadFailedCount += 1;
}

export function incRateLimited429() {
  rateLimited429Count += 1;
}

export function incUnauthorized401() {
  unauthorized401Count += 1;
}

export function incLikeAdded() { likeAddedCount += 1; }
export function incLikeRemoved() { likeRemovedCount += 1; }

export function recordWebVital(name: VitalName, value: number) {
  if (!(name in vitalSum)) return;
  vitalSum[name] += value;
  vitalCount[name] += 1;
}

export function recordFrontendTiming(name: 'feed_load_ms', value: number) {
  if (name === 'feed_load_ms' && Number.isFinite(value) && value >= 0) {
    feedLoadMsSum += value;
    feedLoadMsCount += 1;
  }
}

export function metricsText(): string {
  const lines = [
    `# HELP toybox_request_total Total number of HTTP requests`,
    `# TYPE toybox_request_total counter`,
    `toybox_request_total ${requestCount}`,
    `# HELP toybox_error_total Total number of HTTP 500 errors`,
    `# TYPE toybox_error_total counter`,
    `toybox_error_total ${errorCount}`,
    `# HELP toybox_feed_served_total Total number of feed responses served`,
    `# TYPE toybox_feed_served_total counter`,
    `toybox_feed_served_total ${feedServedCount}`,
    `# HELP toybox_profile_view_total Total number of profile views`,
    `# TYPE toybox_profile_view_total counter`,
    `toybox_profile_view_total ${profileViewCount}`,
    `# HELP toybox_upload_failed_total Total number of failed uploads`,
    `# TYPE toybox_upload_failed_total counter`,
    `toybox_upload_failed_total ${uploadFailedCount}`,
    `# HELP toybox_rate_limited_429_total Total number of 429 responses`,
    `# TYPE toybox_rate_limited_429_total counter`,
    `toybox_rate_limited_429_total ${rateLimited429Count}`,
    `# HELP toybox_unauthorized_401_total Total number of 401 responses`,
    `# TYPE toybox_unauthorized_401_total counter`,
    `toybox_unauthorized_401_total ${unauthorized401Count}`,
    `# HELP toybox_like_added_total Total number of likes added`,
    `# TYPE toybox_like_added_total counter`,
    `toybox_like_added_total ${likeAddedCount}`,
    `# HELP toybox_like_removed_total Total number of likes removed`,
    `# TYPE toybox_like_removed_total counter`,
    `toybox_like_removed_total ${likeRemovedCount}`,
    `# HELP toybox_webvitals_average Aggregated average web vitals by name`,
    `# TYPE toybox_webvitals_average gauge`,
    `toybox_webvitals_average{name="CLS"} ${vitalCount.CLS ? (vitalSum.CLS / vitalCount.CLS) : 0}`,
    `toybox_webvitals_average{name="LCP"} ${vitalCount.LCP ? (vitalSum.LCP / vitalCount.LCP) : 0}`,
    `toybox_webvitals_average{name="FID"} ${vitalCount.FID ? (vitalSum.FID / vitalCount.FID) : 0}`,
    `toybox_webvitals_average{name="INP"} ${vitalCount.INP ? (vitalSum.INP / vitalCount.INP) : 0}`,
    `# HELP toybox_feed_load_ms_average Average feed load time in milliseconds (client-reported)`,
    `# TYPE toybox_feed_load_ms_average gauge`,
    `toybox_feed_load_ms_average ${feedLoadMsCount ? (feedLoadMsSum / feedLoadMsCount) : 0}`,
    `# HELP toybox_process_uptime_seconds Process uptime in seconds`,
    `# TYPE toybox_process_uptime_seconds gauge`,
    `toybox_process_uptime_seconds ${process.uptime().toFixed(0)}`,
    `# HELP toybox_system_loadavg System 1m load average`,
    `# TYPE toybox_system_loadavg gauge`,
    `toybox_system_loadavg ${os.loadavg?.()[0] ?? 0}`
  ];
  return lines.join('\n') + '\n';
}
