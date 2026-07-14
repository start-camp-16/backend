import { expect, it } from 'vitest';
import { renderRankingItems } from '../../../src/features/ranking/ranking-view.js';
import { renderChatSources } from '../../../src/features/chat/chat-sources.js';
import { renderPostForm } from '../../../src/features/board/post-form-view.js';

it('랭킹 순서와 선택 필드를 그대로 표시한다', () => {
  renderRankingItems(document.body,[
    {rank:2,title:'두 번째',address:null,phone:null,image_url:null,thumbnail_url:null},
    {rank:7,title:'일곱 번째',address:'서울',phone:'02',image_url:null,thumbnail_url:null},
  ]);
  expect([...document.querySelectorAll('.rank-number')].map(x=>x.textContent)).toEqual(['2','7']);
  expect(document.body.textContent).not.toContain('null');
});

it('장소 근거는 정보로, 게시글은 링크로 표시한다', () => {
  renderChatSources(document.body,[
    {type:'location',content_id:'1',title:'남산',category:'관광지',district:'중구',address:null},
    {type:'post',post_id:7,title:'후기',tag:'자유'}, {type:'unknown',title:'숨김'},
  ]);
  expect(document.body.querySelectorAll('a')).toHaveLength(1);
  expect(document.querySelector('a').getAttribute('href')).toBe('/posts/7');
  expect(document.body.textContent).not.toContain('숨김');
});

it('게시글 폼은 비밀번호를 미리 채우지 않는다', () => {
  renderPostForm(document.body,{tag:'자유',title:'제목',content:'본문'});
  expect(document.querySelector('[name="password"]').value).toBe('');
  expect(document.querySelector('[name="title"]').value).toBe('제목');
});
