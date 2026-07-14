import { getCategories,getDistricts,getRankings } from './ranking-api.js';
import { parseRankingQuery,toRankingQuery } from './ranking-state.js';
import { renderRankingItems } from './ranking-view.js';
import { renderAsyncState } from '../../ui/async-state.js';
import { renderPagination } from '../../ui/pagination.js';
import './ranking.css';

export function mountRankingPage({outlet,query,signal,navigate}) {
  const state=parseRankingQuery(query);
  outlet.innerHTML=`<section class="ranking-hero"><p class="eyebrow">Seoul city guide</p><h1 class="page-title">서울의 즐거움,<br><span>빠르게 찾아봐요.</span></h1><p class="lede">지역과 카테고리를 선택하면 지금 둘러볼 장소를 순서대로 보여드려요.</p></section><section class="ranking-workspace panel"><form class="ranking-filter"><label>어느 구에서?<select name="district" disabled><option value="">구 선택</option></select></label><label>무엇을 할까요?<select name="category" disabled><option value="">카테고리 선택</option></select></label><button disabled>장소 찾기</button></form><div id="ranking-status" aria-live="polite"></div><div id="ranking-results" class="place-grid"></div><div id="ranking-pagination"></div></section>`;
  const form=outlet.querySelector('form'),status=outlet.querySelector('#ranking-status'),results=outlet.querySelector('#ranking-results'),pager=outlet.querySelector('#ranking-pagination');
  const [districtSelect,categorySelect]=form.querySelectorAll('select'); const submit=form.querySelector('button');
  const fill=(select,items,value)=>{items.forEach(item=>select.add(new Option(item,item))); if(items.includes(value))select.value=value; select.disabled=false};
  const loadRankings=async()=>{ if(!districtSelect.value||!categorySelect.value)return; renderAsyncState(status,{kind:'loading',message:'장소를 찾고 있습니다…'});results.replaceChildren();pager.replaceChildren(); try{const data=await getRankings({district:districtSelect.value,category:categorySelect.value,page:state.page,signal});status.replaceChildren();if(!data.items.length){renderAsyncState(status,{kind:'empty',message:'선택 조건에 해당하는 장소가 없습니다.'});return}renderRankingItems(results,data.items);renderPagination(pager,{page:data.pagination.page,totalPages:data.pagination.total_pages,onPageChange:page=>navigate(`/?${toRankingQuery({district:districtSelect.value,category:categorySelect.value,page})}`)});}catch(error){if(error.name!=='AbortError')renderAsyncState(status,{kind:'error',message:error.message,onRetry:loadRankings})}};
  const loadMeta=async()=>{renderAsyncState(status,{kind:'loading',message:'지역과 카테고리를 불러오고 있습니다…'});try{const [districts,categories]=await Promise.all([getDistricts({signal}),getCategories({signal})]);fill(districtSelect,districts,state.district);fill(categorySelect,categories,state.category);submit.disabled=false;status.replaceChildren();if(districtSelect.value&&categorySelect.value)await loadRankings()}catch(error){if(error.name!=='AbortError')renderAsyncState(status,{kind:'error',message:error.message,onRetry:loadMeta})}};
  const onSubmit=e=>{e.preventDefault();if(!districtSelect.value||!categorySelect.value){renderAsyncState(status,{kind:'error',message:'구와 카테고리를 모두 선택해 주세요.'});return}navigate(`/?${toRankingQuery({district:districtSelect.value,category:categorySelect.value,page:1})}`)};
  form.addEventListener('submit',onSubmit);loadMeta();return()=>form.removeEventListener('submit',onSubmit);
}
