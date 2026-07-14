export function openModal({ title, content, trigger, confirmLabel = '확인', onConfirm }) {
  const dialog = document.createElement('dialog');
  dialog.className = 'modal';
  const heading = document.createElement('h2'); heading.textContent = title;
  const body = document.createElement('div'); body.className = 'modal__body'; body.append(content);
  const actions = document.createElement('div'); actions.className = 'modal__actions';
  const cancel = document.createElement('button'); cancel.type = 'button'; cancel.textContent = '취소';
  const confirm = document.createElement('button'); confirm.type = 'button'; confirm.className = 'button'; confirm.textContent = confirmLabel;
  actions.append(cancel, confirm); dialog.append(heading, body, actions); document.body.append(dialog);
  const close = () => { dialog.remove(); trigger?.focus(); };
  cancel.addEventListener('click', close);
  confirm.addEventListener('click', async () => { if (await onConfirm?.() !== false) close(); });
  dialog.addEventListener('cancel', (event) => { event.preventDefault(); close(); });
  dialog.addEventListener('keydown', (event) => { if (event.key === 'Escape') close(); });
  if (dialog.showModal) dialog.showModal(); else dialog.setAttribute('open', '');
  (dialog.querySelector('input,textarea,select,button') ?? dialog).focus();
  return { dialog, close };
}
