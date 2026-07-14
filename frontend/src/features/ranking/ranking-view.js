import fallback from '../../assets/place-fallback.svg';
import { toCoordinate } from './ranking-map.js';

export function renderRankingItems(container, items, { selectedId = null, onSelect = () => {} } = {}) {
  container.replaceChildren();
  for (const item of items) {
    const article=document.createElement('button'); article.type='button'; article.className='place-card panel';
    article.dataset.contentId=String(item.content_id);
    article.setAttribute('aria-label',`${item.rank}위 ${item.title}`);
    if(String(item.content_id)===String(selectedId)) article.setAttribute('aria-current','true');
    article.addEventListener('click',()=>onSelect(String(item.content_id)));
    const image=document.createElement('img'); image.src=item.thumbnail_url??item.image_url??fallback; image.alt=`${item.title} 대표 이미지`; image.addEventListener('error',()=>{image.src=fallback;},{once:true});
    const rank=document.createElement('strong'); rank.className='rank-number'; rank.textContent=String(item.rank);
    const copy=document.createElement('div'); const title=document.createElement('h3'); title.textContent=item.title; copy.append(title);
    if(item.address){const p=document.createElement('p');p.textContent=item.address;copy.append(p)} if(item.phone){const p=document.createElement('p');p.textContent=item.phone;copy.append(p)}
    if(!toCoordinate(item)){const missing=document.createElement('small');missing.className='map-missing';missing.textContent='지도 위치 없음';copy.append(missing)}
    article.append(rank,image,copy); container.append(article);
  }
}
