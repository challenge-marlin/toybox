import os from 'os';

let requestCount = 0;
let errorCount = 0;
let feedServedCount = 0;
let profileViewCount = 0;
let uploadFailedCount = 0;
let rateLimited429Count = 0;
let unauthorized401Count = 0;

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
    `# HELP toybox_process_uptime_seconds Process uptime in seconds`,
    `# TYPE toybox_process_uptime_seconds gauge`,
    `toybox_process_uptime_seconds ${process.uptime().toFixed(0)}`,
    `# HELP toybox_system_loadavg System 1m load average`,
    `# TYPE toybox_system_loadavg gauge`,
    `toybox_system_loadavg ${os.loadavg?.()[0] ?? 0}`
  ];
  return lines.join('\n') + '\n';
}
