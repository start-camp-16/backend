import { request } from '../../api/client.js';
export function sendChat({message,history},{signal}={}) { return request('/api/chat',{method:'POST',body:{message,history},signal}); }
