export function createChatState() { return { isOpen:false, messages:[], isSending:false, error:null }; }
export function toChatHistory(messages) { return messages.filter(message => message.status === 'sent').map(({role,content})=>({role,content})).slice(-10); }
