import { POST_TAGS } from './board-constants.js';
export function renderPostForm(container, values={}) {
  container.innerHTML=`<form class="editor-form panel" novalidate><label>태그<select name="tag"><option value="">선택</option>${POST_TAGS.map(tag=>`<option value="${tag}">${tag}</option>`).join('')}</select><small data-error="tag"></small></label><label>제목<input name="title" maxlength="100"><small data-error="title"></small></label><label>본문<textarea name="content" maxlength="5000" rows="12"></textarea><small data-error="content"></small></label><label>비밀번호<input name="password" type="password" minlength="4" maxlength="20" autocomplete="new-password"><small data-error="password"></small></label><div data-form-error role="alert"></div><button>저장하기</button></form>`;
  const form=container.querySelector('form');form.elements.tag.value=values.tag??'';form.elements.title.value=values.title??'';form.elements.content.value=values.content??'';return form;
}
export function showFormErrors(form,errors){form.querySelectorAll('[data-error]').forEach(node=>node.textContent=errors[node.dataset.error]??'');const first=Object.keys(errors)[0];if(first)form.elements[first]?.focus()}
