import { demoRequest } from '../request';

export function UploadFiles(headers: any, data: any) {
  return demoRequest({
    url: '/upload',
    method: 'post',
    headers,
    data
  });
}

export function UploadTumorHospitalFiles(headers: any, data: any) {
  return demoRequest({
    url: '/uploadTumorHospital',
    method: 'post',
    headers,
    data
  });
}

export function GenerateTumorHospital(data: any) {
  return demoRequest({
    url: '/generateTumorHospital',
    method: 'post',
    data
  });
}

export function UploadSixthHospitalFiles(headers: any, data: any) {
  return demoRequest({
    url: '/uploadSixthHospital',
    method: 'post',
    headers,
    data
  });
}

export function GenerateSixthHospital(data: any) {
  return demoRequest({
    url: '/generateSixthHospital',
    method: 'post',
    data
  });
}

export function quickUploadFiles() {
  return demoRequest({
    url: '/quickupload',
    method: 'get'
  });
}

export function PostParams(data: any) {
  return demoRequest({
    url: '/params',
    method: 'post',
    headers: { 'Content-Type': 'application/json' },
    data
  });
}

export function GenerateDS(data: any) {
  return demoRequest({
    url: '/generate',
    method: 'post',
    timeout: 10 * 60 * 1000,
    headers: { 'Content-Type': 'application/json' },
    data
  });
}

export function PostComment(data: any) {
  return demoRequest({
    url: '/comment',
    method: 'post',
    headers: { 'Content-Type': 'application/json' },
    data
  });
}
