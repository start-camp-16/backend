import fallback from '../../assets/place-fallback.svg';
export function renderRankingItems(container, items) {
  container.replaceChildren();
  for (const item of items) {
    const article=document.createElement('article'); article.className='place-card panel';
    const image=document.createElement('img'); image.src=item.thumbnail_url??item.image_url??fallback; image.alt=`${item.title} 대표 이미지`; image.addEventListener('error',()=>{image.src=fallback;},{once:true});
    const rank=document.createElement('strong'); rank.className='rank-number'; rank.textContent=String(item.rank);
    const copy=document.createElement('div'); const title=document.createElement('h3'); title.textContent=item.title; copy.append(title);
    if(item.address){const p=document.createElement('p');p.textContent=item.address;copy.append(p)} if(item.phone){const p=document.createElement('p');p.textContent=item.phone;copy.append(p)}
    article.append(rank,image,copy); container.append(article);
  }
}
