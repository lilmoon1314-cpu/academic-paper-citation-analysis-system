const API = 'http://127.0.0.1:5000';

var COMMUNITY_COLORS = [
  '#5c7cfa','#fac858','#ee6666','#91cc75',
  '#73c0de','#fc8452','#9a60b4','#3ba272',
  '#ea7ccc','#60c0dd','#f59e0b','#10b981'
];
var EDGE_COLORS = {
  out:'#5c7cfa', in:'#ee6666',
  forward:'#91cc75', backward:'#fac858',
  lateral:'#8b92b3ff', other:'#798098ff'
};

function communityColor(c){ return COMMUNITY_COLORS[Math.abs(c||0)%COMMUNITY_COLORS.length]; }

var _prMax = 0, _prMin = Infinity;

function formatPR(v){
  if(!v||v<=0) return '< 1e-9';
  if(v>=0.001) return v.toFixed(6);
  return v.toExponential(3);
}

function computeSizes(nodes, minPx, maxPx){
  minPx = minPx || 10;
  maxPx = maxPx || 50;
  var vals = nodes.map(function(n){return n.pagerank||0;});
  var min  = Math.min.apply(null, vals);
  var max  = Math.max.apply(null, vals);
  _prMax = max; _prMin = min;
  return nodes.map(function(n){
    var ratio = max===min ? 0.5 : (n.pagerank-min)/(max-min);
    return minPx + Math.sqrt(ratio)*(maxPx-minPx);
  });
}

function prPercent(v){
  if(_prMax===_prMin) return 50;
  return Math.round(((v||0)-_prMin)/(_prMax-_prMin)*100);
}

var chart          = null;
var currentNodes   = [];
var currentEdges   = [];
var currentCenterId= null;
var currentLayout  = 'force';
var dataCache      = new Map();
var renderBusy     = false;
var suggestTimer   = null;
var allYears       = [];

function initChart(){
  var dom = document.getElementById('citation-chart');
  chart = echarts.init(dom, null, {renderer:'canvas'});
  chart.on('click', function(p){ if(p.dataType==='node') handleNodeClick(p.data); });
  window.addEventListener('resize', function(){chart.resize();});
}

function applyCommunityForceLayout(nodes, centerX, centerY, communityEdges, options) {
  options = options || {};
  var repulsion = options.repulsion || 800;
  var gravity = options.gravity || 0.05;
  var maxIterations = options.maxIterations || 60;
  var maxDistance = options.maxDistance || 600;
  
  var nodeMap = {};
  nodes.forEach(function(n, i) {
    n.vx = 0;
    n.vy = 0;
    nodeMap[n.id] = n;
    
    if (!n.x || !n.y) {
      var angle = Math.random() * 2 * Math.PI;
      var radius = Math.random() * 200;
      n.x = centerX + Math.cos(angle) * radius;
      n.y = centerY + Math.sin(angle) * radius;
    }
  });
  
  for (var iter = 0; iter < maxIterations; iter++) {
    nodes.forEach(function(n) {
      n.vx = 0;
      n.vy = 0;
    });
    
    nodes.forEach(function(n1, i) {
      nodes.forEach(function(n2, j) {
        if (i >= j) return;
        
        var dx = n2.x - n1.x;
        var dy = n2.y - n1.y;
        var distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance > 0) {
          var minDistance = 120;
          if (distance < minDistance) {
            var force = repulsion * (minDistance - distance) / distance;
          } else {
            var force = repulsion / (distance * distance);
          }
          var fx = force * dx / distance;
          var fy = force * dy / distance;
          
          n1.vx -= fx;
          n1.vy -= fy;
          n2.vx += fx;
          n2.vy += fy;
        }
      });
      
      var dxToCenter = centerX - n1.x;
      var dyToCenter = centerY - n1.y;
      var distToCenter = Math.sqrt(dxToCenter * dxToCenter + dyToCenter * dyToCenter);
      
      if (distToCenter > maxDistance) {
        var pullForce = gravity * (distToCenter - maxDistance);
        n1.vx += pullForce * dxToCenter / distToCenter;
        n1.vy += pullForce * dyToCenter / distToCenter;
      }
    });
    
    var connectedPairs = [];
    communityEdges.forEach(function(e) {
      var source = nodeMap[e.source];
      var target = nodeMap[e.target];
      if (source && target) {
        connectedPairs.push([source, target]);
      }
    });
    
    connectedPairs.forEach(function(pair) {
      var n1 = pair[0], n2 = pair[1];
      var dx = n2.x - n1.x;
      var dy = n2.y - n1.y;
      var distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance > 0) {
        var idealDistance = 200;
        var springForce = 0.04 * (distance - idealDistance);
        
        n1.vx += springForce * dx / distance;
        n1.vy += springForce * dy / distance;
        n2.vx -= springForce * dx / distance;
        n2.vy -= springForce * dy / distance;
      }
    });
    
    nodes.forEach(function(n) {
      var speed = Math.sqrt(n.vx * n.vx + n.vy * n.vy);
      if (speed > 15) {
        n.vx = n.vx * 15 / speed;
        n.vy = n.vy * 15 / speed;
      }
      
      n.x += n.vx;
      n.y += n.vy;
      
      var dx = n.x - centerX;
      var dy = n.y - centerY;
      var dist = Math.sqrt(dx * dx + dy * dy);
      if (dist > maxDistance) {
        n.x = centerX + dx * maxDistance / dist;
        n.y = centerY + dy * maxDistance / dist;
      }
    });
  }
  
  return nodes;
}

function layoutCommunity(nodes){
  var comms = {};
  nodes.forEach(function(n){
    if(!comms[n.community]) comms[n.community]={nodes:[],size:0};
    comms[n.community].nodes.push(n);
    comms[n.community].size++;
  });
  var sorted = Object.entries(comms).sort(function(a,b){return b[1].size-a[1].size;});
  var totalNodes = nodes.length;
  var communityCount = sorted.length;

  var baseRadius = Math.max(400, Math.min(1200, totalNodes * 12));
  if (communityCount <= 2) baseRadius = Math.max(300, totalNodes * 8);
  if (communityCount === 1) baseRadius = 0;

  sorted.forEach(function(entry, i){
    var c = entry[1];
    var angle = (i / communityCount) * 2 * Math.PI - Math.PI/2;
    c.cx = Math.cos(angle) * baseRadius;
    c.cy = Math.sin(angle) * baseRadius;
  });

  var communityEdgesMap = {};
  sorted.forEach(function(entry) {
    var commId = entry[0];
    var c = entry[1];
    var nodeIds = new Set(c.nodes.map(n => n.id));
    
    communityEdgesMap[commId] = currentEdges.filter(function(e) {
      return nodeIds.has(e.source) && nodeIds.has(e.target);
    });
  });

  sorted.forEach(function(entry){
    var commId = entry[0];
    var c = entry[1];
    var communityEdges = communityEdgesMap[commId] || [];
    
    c.nodes.sort(function(a,b){return (b.pagerank||0)-(a.pagerank||0);});
    
    var nodeCount = c.nodes.length;
     var communityRadius = Math.max(300, Math.min(800, Math.sqrt(nodeCount) * 100));
    
    if (nodeCount <= 3) {
        c.nodes.forEach(function(n, idx) {
           var angle = (idx / nodeCount) * 2 * Math.PI;
           n.x = c.cx + Math.cos(angle) * 150;
           n.y = c.cy + Math.sin(angle) * 150;
         });
      } else {
        applyCommunityForceLayout(c.nodes, c.cx, c.cy, communityEdges, {
          repulsion: Math.max(500, Math.min(1500, 20000 / nodeCount)),
          gravity: 0.08,
          maxIterations: 50,
          maxDistance: communityRadius
        });
      }
  });

  var center = null;
  for (var i = 0; i < nodes.length; i++) {
    if (nodes[i].isCenter) { center = nodes[i]; break; }
  }
  if(center){center.x=0;center.y=0;}
  return nodes;
}

function layoutTimeline(nodes){
  var yearSet = {};
  nodes.forEach(function(n){
    var y = n.year||0;
    if(y>0) yearSet[y]=true;
  });
  var years = Object.keys(yearSet).map(Number).sort(function(a,b){return a-b;});
  allYears = years;
  var yMin = years[0]||1990, yMax = years[years.length-1]||2024;
  var yearSpan = Math.max(yMax - yMin, 1);
  var W = Math.max(2400, yearSpan * 80);
  var yearCols = {};
  years.forEach(function(y){yearCols[y]=[];});
  nodes.forEach(function(n){
    var y = n.year||yMin;
    if(!yearCols[y]) yearCols[y]=[];
    yearCols[y].push(n);
  });
  Object.entries(yearCols).forEach(function(entry){
    var y = entry[0], ns = entry[1];
    var xPos = ((y-yMin)/yearSpan)*W - W/2;
    ns.sort(function(a,b){return (b.pagerank||0)-(a.pagerank||0);});
    var spacing = Math.max(80, Math.min(160, 1200 / ns.length));
    ns.forEach(function(n, i){
      n.x = xPos + (Math.random()-0.5)*20;
      n.y = (i-(ns.length-1)/2)*spacing;
    });
  });
  return nodes;
}

function layoutRadial(nodes, centerId){
  var adj = {};
  nodes.forEach(function(n){adj[n.id]=[];});
  currentEdges.forEach(function(e){
    if(adj[e.source]) adj[e.source].push(e.target);
    if(adj[e.target]) adj[e.target].push(e.source);
  });
  var dist = {}, q = [centerId];
  dist[centerId] = 0;
  while(q.length){
    var cur = q.shift();
    (adj[cur]||[]).forEach(function(nb){
      if(dist[nb]===undefined){ dist[nb]=dist[cur]+1; q.push(nb); }
    });
  }
  var rings = {};
  nodes.forEach(function(n){
    var d = dist[n.id]!=null ? dist[n.id] : 99;
    if(!rings[d]) rings[d]=[];
    rings[d].push(n);
  });
  var maxRing = 0;
  Object.keys(rings).forEach(function(k){ maxRing = Math.max(maxRing, parseInt(k)); });
  Object.entries(rings).forEach(function(entry){
    var d = parseInt(entry[0]), ns = entry[1];
    var r = d * 260;
    ns.sort(function(a,b){return (b.pagerank||0)-(a.pagerank||0);});
    ns.forEach(function(n, i){
      var a = (i/ns.length)*2*Math.PI;
      var jit = r*0.03;
      n.x = Math.cos(a)*r+(Math.random()-.5)*jit;
      n.y = Math.sin(a)*r+(Math.random()-.5)*jit;
    });
  });
  var center = null;
  for (var i = 0; i < nodes.length; i++) {
    if (nodes[i].id === centerId) { center = nodes[i]; break; }
  }
  if(center){center.x=0;center.y=0;}
  return nodes;
}

function renderChart(nodes, edges, layoutOverride){
  document.getElementById('chart-placeholder').style.display='none';
  var layout = layoutOverride || currentLayout;

  var isNonForce = (layout==='community'||layout==='timeline'||layout==='radial');
  var sizes = isNonForce ? computeSizes(nodes, 6, 24) : computeSizes(nodes, 10, 50);

  var lnodes = nodes.map(function(n){return Object.assign({}, n);});
  if(layout==='community')       lnodes = layoutCommunity(lnodes);
  else if(layout==='timeline')   lnodes = layoutTimeline(lnodes);
  else if(layout==='radial')     lnodes = layoutRadial(lnodes, currentCenterId);

  var tlOverlay = document.getElementById('timeline-overlay');
  if(layout==='timeline'){
    tlOverlay.classList.add('show');
    updateTimelineSlider(nodes);
  } else {
    tlOverlay.classList.remove('show');
  }

  var forceCfg;
  if (layout === 'community') {
    forceCfg = {
      repulsion: [300, 1000],
      gravity: 0.01,
      edgeLength: [120, 300],
      friction: 0.85,
      layoutAnimation: false,
      coolingFactor: 0.99,
      maxIteration: 100
    };
  } else if (layout === 'radial') {
    forceCfg = {
      repulsion: [200, 600],
      gravity: 0.01,
      edgeLength: [100, 250],
      friction: 0.85,
      layoutAnimation: false,
      coolingFactor: 0.99,
      maxIteration: 100
    };
  } else if (layout === 'timeline') {
    forceCfg = {
      repulsion: [100, 400],
      gravity: 0.01,
      edgeLength: [60, 150],
      friction: 0.9,
      layoutAnimation: false,
      coolingFactor: 0.99,
      maxIteration: 50
    };
  } else {
    forceCfg = {
      repulsion: [800, 2500],
      gravity: 0.08,
      edgeLength: [80, 200],
      friction: 0.45,
      layoutAnimation: true,
      coolingFactor: 0.94,
      maxIteration: 800
    };
  }

  var option = {
    backgroundColor:'#0d1020',
    tooltip:{
      trigger:'item', confine:true,
      backgroundColor:'rgba(20,25,50,0.95)',
      borderColor:'#2d3460', borderWidth:1,
      textStyle:{color:'#c8d4f0'},
      formatter: function(p){
        if(p.dataType!=='node') return '';
        var d=p.data;
        return '<div style="max-width:260px;line-height:1.7">'+
          '<b style="font-size:13px;color:#e0e6f0">'+escHtml(d.name)+'</b><br/>'+
          '<span style="color:#5a6890;font-size:11px">'+escHtml(d.authors||'')+'</span><br/>'+
          '<span style="color:#7a8ab0;font-size:11px">'+
            '📅 '+ (d.year||'?') +' &nbsp;·&nbsp;'+
            '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;'+
              'background:'+communityColor(d.community)+';vertical-align:middle"></span> '+
            escHtml(d.communityLabel||'社区'+d.community)+
          '</span><br/>'+
          '<span style="color:#5c7cfa;font-size:11px">PageRank: <b>'+formatPR(d.pagerank)+'</b></span>'+
        '</div>';
      }
    },
    series:[{
      type:'graph', layout:'force',
      force: forceCfg,
      roam:true, focusNodeAdjacency:true,
      animation:false,
      data: lnodes.map(function(n,i){
        return Object.assign({}, n, {
          symbolSize: sizes[i],
          x: n.x, y: n.y,
          fixed: (layout==='community'||layout==='timeline'||layout==='radial'),
          itemStyle:{
            color:      n.isCenter ? '#ff4757' : communityColor(n.community),
            borderColor: n.isCenter ? '#fff' : 'rgba(255,255,255,0.15)',
            borderWidth: n.isCenter ? 3 : 1,
            shadowBlur:  n.isCenter ? 30 : (sizes[i]>30 ? 12 : 4),
            shadowColor: n.isCenter ? 'rgba(255,71,87,0.7)' : communityColor(n.community)+'55'
          },
          label:{
            show: n.isCenter || (isNonForce ? sizes[i] > 16 : sizes[i] > 28),
            formatter: function(d){ var t=d.data.name||''; return t.length>18?t.slice(0,18)+'…':t; },
            fontSize:  n.isCenter ? 13 : 10,
            fontWeight: n.isCenter ? 'bold' : 'normal',
            color: '#c8d4f0',
            position:'right',
            backgroundColor:'rgba(13,16,32,0.8)',
            padding:[2,6], borderRadius:4
          }
        });
      }),
      labelLayout:{
        hideOverlap: true,
        moveOverlap: 'shiftY'
      },
      links: edges.map(function(e){
        return {
          source:e.source, target:e.target,
          lineStyle:{
            color:   EDGE_COLORS[e.direction]||EDGE_COLORS.other,
            width:   e.direction==='lateral'||e.direction==='other' ? 0.8 : 1.5,
            curveness: 0.08,
            opacity: e.direction==='lateral'||e.direction==='other' ? 0.25 : 0.65
          },
          symbol:['none','arrow'], symbolSize:[0,5]
        };
      }),
      emphasis:{
        focus:'adjacency',
        label:{show:true,fontSize:12},
        lineStyle:{width:2.5, opacity:1}
      },
      scaleLimit:{min:0.1, max:12}
    }]
  };

  chart.setOption(option, true);
  updateLegend(nodes);
  updateStats(nodes, edges);
}

function updateTimelineSlider(nodes){
  var years = nodes.map(function(n){return n.year||0;}).filter(function(y){return y>1900;});
  if(!years.length) return;
  var min = Math.min.apply(null, years), max = Math.max.apply(null, years);
  var slider = document.getElementById('year-slider');
  slider.min = min; slider.max = max; slider.value = max;
  document.getElementById('year-display').textContent = max;
}

document.getElementById('year-slider').addEventListener('input', function(){
  var yr = parseInt(this.value);
  document.getElementById('year-display').textContent = yr;
  if(!currentNodes.length) return;
  var option = chart.getOption();
  var series = option.series[0];
  if(!series) return;
  series.data = series.data.map(function(n){
    return Object.assign({}, n, {
      itemStyle: Object.assign({}, n.itemStyle, {
        opacity: (n.year||0) <= yr ? 1 : 0.08
      }),
      label: Object.assign({}, n.label, { show: (n.year||0)<=yr && (n.isCenter||false) })
    });
  });
  chart.setOption({series:[series]}, false);
});

function updateLegend(nodes){
  var commSet = {};
  nodes.forEach(function(n){ commSet[n.community]=true; });
  var comms = Object.keys(commSet).map(Number).sort(function(a,b){return a-b;});
  var counts = {};
  nodes.forEach(function(n){ counts[n.community]=(counts[n.community]||0)+1; });

  document.getElementById('legend-communities').innerHTML = comms.slice(0,10).map(function(c){
    var node = null;
    for (var i = 0; i < nodes.length; i++) {
      if (nodes[i].community === c) { node = nodes[i]; break; }
    }
    var label = (node&&node.communityLabel) ? node.communityLabel : ('社区 '+c);
    return '<div class="leg-item">'+
      '<div class="leg-dot" style="background:'+communityColor(c)+'"></div>'+
      '<span title="'+escHtml(label)+'" style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+escHtml(label)+'</span>'+
      '<span style="color:#2d3460;font-size:10px">'+(counts[c]||0)+'</span>'+
    '</div>';
  }).join('');
}

function updateStats(nodes, edges){
  var commSet = {};
  nodes.forEach(function(n){ commSet[n.community]=true; });
  var comms = Object.keys(commSet).length;
  document.getElementById('ts-nodes').textContent = nodes.length;
  document.getElementById('ts-edges').textContent = edges.length;
  document.getElementById('ts-comms').textContent = comms;
}

async function fetchSuggestions(keyword){
  if(!keyword.trim()){ hideSuggest(); return; }
  try{
    var res  = await fetch(API+'/search_suggest?q='+encodeURIComponent(keyword));
    var data = await res.json();
    showSuggest(data);
  } catch(e){ hideSuggest(); }
}

function showSuggest(items){
  var dd = document.getElementById('suggest-dropdown');
  if(!items.length){
    dd.innerHTML='<div class="suggest-empty">未找到相关论文，尝试英文关键词</div>';
    dd.classList.add('show');
    return;
  }
  dd.innerHTML = items.map(function(p){
    return '<div class="suggest-item" onclick="selectPaper(\''+p.id+'\',\''+escHtml(p.title)+'\')">'+
      '<div class="suggest-title">'+escHtml(p.title)+'</div>'+
      '<div class="suggest-meta">'+
        escHtml((p.authors||'').split(';')[0]+(p.authors&&p.authors.includes(';')?' et al.':''))+
        ' · '+(p.year||'?')+
        '<span class="suggest-pr">PR: '+formatPR(p.pagerank)+'</span>'+
      '</div>'+
    '</div>';
  }).join('');
  dd.classList.add('show');
}
function hideSuggest(){ document.getElementById('suggest-dropdown').classList.remove('show'); }

async function selectPaper(id, title){
  if(renderBusy) return;
  renderBusy = true;
  hideSuggest();
  document.getElementById('search-input').value = title;
  currentCenterId = id;

  var hops     = parseInt(document.getElementById('hops-select').value);
  var maxNodes = parseInt(document.getElementById('nodes-select').value);
  var cacheKey = id+'_'+hops+'_'+maxNodes;

  showLoading(true, '请求网络数据...', '正在从数据库检索引用关系');

  try{
    var data;
    if(dataCache.has(cacheKey)){
      data = dataCache.get(cacheKey);
    } else {
      showLoading(true, '查询引用网络...', '最多 '+maxNodes+' 节点 / '+hops+' 跳');
      var res = await fetch(API+'/graph?id='+id+'&hops='+hops+'&max_nodes='+maxNodes);
      if(!res.ok) throw new Error('HTTP '+res.status);
      data = await res.json();
      if(!data.nodes.length){ alert('该论文暂无引用关系数据'); return; }
      dataCache.set(cacheKey, data);
      if(dataCache.size>12){ dataCache.delete(dataCache.keys().next().value); }
    }

    currentNodes = data.nodes;
    currentEdges = data.edges;

    showLoading(true, '计算布局...', data.nodes.length+' 节点 / '+data.edges.length+' 边');
    await new Promise(function(r){setTimeout(r,20);});

    renderChart(currentNodes, currentEdges);
    var center = null;
    for (var i = 0; i < currentNodes.length; i++) {
      if (currentNodes[i].id === id) { center = currentNodes[i]; break; }
    }
    if (!center) center = currentNodes[0];
    handleNodeClick(center);

    fetchNetworkMetrics();
    fetchFrontierPapers();

  } catch(e){
    alert('构建网络失败，请确认后端已启动：'+e.message);
    console.error(e);
  } finally {
    showLoading(false);
    renderBusy = false;
  }
}

async function handleNodeClick(nodeData){
  currentCenterId = nodeData.id;
  updateNodeInfo(nodeData);

  var idx = -1;
  for (var i = 0; i < currentNodes.length; i++) {
    if (currentNodes[i].id === nodeData.id) { idx = i; break; }
  }
  if(idx>=0) chart.dispatchAction({type:'focusNodeAdjacency', seriesIndex:0, dataIndex:idx});

  document.getElementById('recommendation-list').innerHTML=
    '<div class="default-msg">⏳ 加载推荐中...</div>';
  try{
    var res  = await fetch(API+'/recommend?id='+nodeData.id);
    var recs = await res.json();
    updateRecommendations(recs);
  } catch(e){
    document.getElementById('recommendation-list').innerHTML=
      '<div class="default-msg">推荐加载失败</div>';
  }
}

var _currentPaperName = '';

function updateNodeInfo(n){
  _currentPaperName = n.name||'';

  var sameComm = currentNodes.filter(function(x){return x.community===n.community;})
                               .sort(function(a,b){return (b.pagerank||0)-(a.pagerank||0);});
  var commRank = -1;
  for (var i = 0; i < sameComm.length; i++) {
    if (sameComm[i].id === n.id) { commRank = i+1; break; }
  }
  var sortedAll = currentNodes.slice().sort(function(a,b){return (b.pagerank||0)-(a.pagerank||0);});
  var allRank = -1;
  for (var j = 0; j < sortedAll.length; j++) {
    if (sortedAll[j].id === n.id) { allRank = j+1; break; }
  }

  var pct = prPercent(n.pagerank||0);
  var ssHome='https://www.semanticscholar.org/';
  var gsHome='https://scholar.google.com/';
  var arxivHome='https://arxiv.org/search/';

  document.getElementById('node-details').innerHTML =
    '<div class="info-item">'+
      '<span class="info-label">标题</span>'+
      '<span class="info-title">'+escHtml(n.name)+'</span>'+
    '</div>'+
    '<div class="info-item">'+
      '<span class="info-label">作者</span>'+
      '<span class="info-value">'+escHtml(n.authors||'未知')+'</span>'+
    '</div>'+
    '<div class="info-item">'+
      '<span class="info-label">年份</span>'+
      '<span class="info-value">📅 '+(n.year||'未知')+'</span>'+
    '</div>'+
    '<div class="metric-grid">'+
      '<div class="metric-card">'+
        '<div class="metric-val">#'+allRank+'</div>'+
        '<div class="metric-lbl">网络影响力排名</div>'+
      '</div>'+
      '<div class="metric-card">'+
        '<div class="metric-val" style="color:'+communityColor(n.community)+'">#'+commRank+'</div>'+
        '<div class="metric-lbl">社区内排名</div>'+
      '</div>'+
    '</div>'+
    '<div class="pr-bar-wrap">'+
      '<div class="pr-bar-label">'+
        '<span class="pr-bar-text">PageRank 影响力</span>'+
        '<span class="pr-bar-val">'+formatPR(n.pagerank||0)+'</span>'+
      '</div>'+
      '<div class="pr-bar-bg">'+
        '<div class="pr-bar-fill" style="width:'+pct+'%"></div>'+
      '</div>'+
    '</div>'+
    '<div class="info-item">'+
      '<span class="info-label">研究领域</span>'+
      '<span class="info-value">'+
        '<span class="comm-dot" style="background:'+communityColor(n.community)+'"></span>'+
        escHtml(n.communityLabel||'社区 '+n.community)+
      '</span>'+
    '</div>'+
    '<div style="margin-top:8px">'+
      '<div class="link-hint">💡 请先复制论文名称，再打开对应平台搜索</div>'+
      '<button class="copy-btn" id="copy-title-btn" onclick="copyTitle()">📋 复制论文名称</button>'+
      '<div class="link-row">'+
        '<a class="paper-link" style="background:#1e63b0" href="'+ssHome+'" target="_blank">Semantic Scholar</a>'+
        '<a class="paper-link" style="background:#c53929" href="'+gsHome+'" target="_blank">Google Scholar</a>'+
        '<a class="paper-link" style="background:#8b1a1a" href="'+arxivHome+'" target="_blank">arXiv</a>'+
      '</div>'+
    '</div>';
}

function copyTitle(){
  if(!_currentPaperName) return;
  navigator.clipboard.writeText(_currentPaperName).then(function(){
    var btn=document.getElementById('copy-title-btn');
    if(!btn) return;
    btn.textContent='✅ 已复制！'; btn.classList.add('copied');
    setTimeout(function(){ btn.textContent='📋 复制论文名称'; btn.classList.remove('copied'); },2000);
  }).catch(function(){prompt('请手动复制：',_currentPaperName);});
}

function updateRecommendations(recs){
  var list = document.getElementById('recommendation-list');
  if(!recs||!recs.length){
    list.innerHTML='<div class="default-msg">暂无推荐</div>'; return;
  }

  list.innerHTML = recs.map(function(r,i){
    return '<div class="rec-item" onclick="selectPaper(\''+r.id+'\',\''+escHtml(r.name)+'\')"'+
         ' style="border-left-color:'+communityColor(r.community)+'">'+
      '<span class="rec-num">#'+(i+1)+'</span>'+
      '<div class="rec-title">'+escHtml(r.name)+'</div>'+
      '<span class="rec-authors">'+escHtml((r.authors||'').split(';')[0])+'</span>'+
      '<span style="font-size:11px;color:#4a5580">📅 '+(r.year||'?')+'</span>'+
      '<div class="rec-tags">'+
        (r.recReason?'<span class="rec-tag reason">🔗 '+escHtml(r.recReason)+'</span>':'')+
        (r.sharedCitations?'<span class="rec-tag shared">共享引用×'+r.sharedCitations+'</span>':'')+
        '<span class="rec-tag community">'+
          '<span class="comm-dot" style="background:'+communityColor(r.community)+'"></span>'+
          escHtml(r.communityLabel||'社区'+r.community)+
        '</span>'+
      '</div>'+
      '<span class="rec-score">PR:'+formatPR(r.pagerank)+'</span>'+
    '</div>';
  }).join('');
}

function highlightChain(direction){
  if(!currentCenterId||!chart) return;
  var edgeSet = {};
  var nodeSet = {};
  nodeSet[currentCenterId] = true;

  var frontier = [currentCenterId];
  for(var hop=0;hop<6;hop++){
    var next=[];
    frontier.forEach(function(fid){
      currentEdges.forEach(function(e){
        if(direction==='upstream' && e.target===fid && !nodeSet[e.source]){
          nodeSet[e.source]=true; next.push(e.source);
          edgeSet[e.source+'_'+e.target]=true;
        }
        if(direction==='downstream' && e.source===fid && !nodeSet[e.target]){
          nodeSet[e.target]=true; next.push(e.target);
          edgeSet[e.source+'_'+e.target]=true;
        }
      });
    });
    frontier=next;
    if(!frontier.length) break;
  }

  var option = chart.getOption();
  var series = option.series[0];
  series.data = series.data.map(function(n){
    return Object.assign({}, n, {itemStyle: Object.assign({}, n.itemStyle, {opacity: nodeSet[n.id] ? 1 : 0.1})
    });
  });
  series.links = series.links.map(function(e){
    return Object.assign({}, e, {lineStyle: Object.assign({}, e.lineStyle, {
      opacity: edgeSet[e.source+'_'+e.target] ? 0.9 : 0.05,
      width:   edgeSet[e.source+'_'+e.target] ? 2.5 : 0.5
    })});
  });
  chart.setOption({series:[series]},false);
}

function showLoading(v, text, sub){
  document.getElementById('loading').classList.toggle('show',v);
  if(text) document.getElementById('loading-text').textContent=text;
  if(sub)  document.getElementById('loading-sub').textContent=sub;
}

function escHtml(s){
  return String(s||'')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

async function fetchNetworkMetrics(){
  if(!currentCenterId) return;
  var hops     = parseInt(document.getElementById('hops-select').value);
  var maxNodes = parseInt(document.getElementById('nodes-select').value);
  try{
    var res  = await fetch(API+'/network_metrics?id='+currentCenterId+'&hops='+hops+'&max_nodes='+maxNodes);
    var data = await res.json();
    renderMetrics(data);
  } catch(e){
    document.getElementById('metrics-content').innerHTML='<div class="default-msg">指标加载失败</div>';
  }
}

function renderMetrics(data){
  var d = data.density;
  var densityLabel = d < 0.01 ? '稀疏' : d < 0.05 ? '中等' : d < 0.15 ? '较密' : '密集';
  var densityPct = Math.min(100, Math.round(d * 2000));

  var mod = data.modularity;
  var modLabel = mod < 0.1 ? '弱社区结构' : mod < 0.3 ? '中等社区结构' : '强社区结构';
  var modPct = Math.min(100, Math.max(0, Math.round((mod + 0.5) * 100)));

  var html = '';

  html += '<div class="metrics-grid">';
  html += '<div class="metric-box">';
  html += '<div class="metric-box-val">'+data.summary.nodes+'</div>';
  html += '<div class="metric-box-lbl">节点数</div>';
  html += '</div>';
  html += '<div class="metric-box">';
  html += '<div class="metric-box-val">'+data.summary.edges+'</div>';
  html += '<div class="metric-box-lbl">引用边数</div>';
  html += '</div>';
  html += '<div class="metric-box">';
  html += '<div class="metric-box-val">'+data.density.toFixed(4)+'</div>';
  html += '<div class="metric-box-lbl">网络密度</div>';
  html += '<div class="metric-box-sub">'+densityLabel+'</div>';
  html += '</div>';
  html += '<div class="metric-box">';
  html += '<div class="metric-box-val">'+data.avg_path_length+'</div>';
  html += '<div class="metric-box-lbl">平均路径长度</div>';
  html += '</div>';
  html += '<div class="metric-box">';
  html += '<div class="metric-box-val">'+data.largest_component.size+'</div>';
  html += '<div class="metric-box-lbl">最大连通分量</div>';
  html += '<div class="metric-box-sub">'+data.largest_component.percentage+'% / '+data.largest_component.total_components+'个分量</div>';
  html += '</div>';
  html += '<div class="metric-box">';
  html += '<div class="metric-box-val">'+data.modularity.toFixed(3)+'</div>';
  html += '<div class="metric-box-lbl">社区模块度</div>';
  html += '<div class="metric-box-sub">'+modLabel+'</div>';
  html += '</div>';
  html += '</div>';

  html += '<div class="metric-bar-wrap">';
  html += '<div class="metric-bar-label"><span>网络密度</span><span>'+densityLabel+'</span></div>';
  html += '<div class="metric-bar-bg"><div class="metric-bar-fill" style="width:'+densityPct+'%;background:#5c7cfa"></div></div>';
  html += '</div>';
  html += '<div class="metric-bar-wrap">';
  html += '<div class="metric-bar-label"><span>社区模块度</span><span>'+modLabel+'</span></div>';
  html += '<div class="metric-bar-bg"><div class="metric-bar-fill" style="width:'+modPct+'%;background:#91cc75"></div></div>';
  html += '</div>';

  html += '<div style="font-size:11px;font-weight:700;color:#7a8ab0;margin:8px 0 4px;">🏆 中心性 Top 10</div>';
  html += '<div class="top10-list">';
  data.top10_centrality.forEach(function(n, i){
    var rankClass = i===0?'gold':i===1?'silver':i===2?'bronze':'';
    html += '<div class="top10-item" onclick="selectPaper(\''+n.id+'\',\''+escHtml(n.name)+'\')">';
    html += '<span class="top10-rank '+rankClass+'">'+(i+1)+'</span>';
    html += '<span class="top10-name" title="'+escHtml(n.name)+'">'+escHtml(n.name)+'</span>';
    html += '<span class="top10-pr">PR:'+formatPR(n.pagerank)+'</span>';
    html += '</div>';
  });
  html += '</div>';

  document.getElementById('metrics-content').innerHTML = html;
}

async function fetchFrontierPapers(){
  if(!currentCenterId) return;
  var hops     = parseInt(document.getElementById('hops-select').value);
  var maxNodes = parseInt(document.getElementById('nodes-select').value);
  try{
    var res  = await fetch(API+'/frontier_papers?id='+currentCenterId+'&hops='+hops+'&max_nodes='+maxNodes);
    var data = await res.json();
    renderFrontier(data);
  } catch(e){
    document.getElementById('frontier-content').innerHTML='<div class="default-msg">前沿分析加载失败</div>';
  }
}

function renderFrontier(data){
  var html = '';

  if(data.latest_papers && data.latest_papers.length){
    html += '<div class="frontier-section">';
    html += '<div class="frontier-section-title"><span class="frontier-section-icon">📅</span>最新论文</div>';
    data.latest_papers.forEach(function(p){
      html += '<div class="frontier-item" onclick="selectPaper(\''+p.id+'\',\''+escHtml(p.name)+'\')">';
      html += '<div class="frontier-item-name">'+escHtml(p.name)+'</div>';
      html += '<div class="frontier-item-meta">';
      html += '<span>📅 '+p.year+'</span>';
      html += '<span style="color:#5c7cfa">PR:'+formatPR(p.pagerank)+'</span>';
      html += '<span class="frontier-badge community-badge">'+
        '<span class="comm-dot" style="background:'+communityColor(p.community)+'"></span>'+
        escHtml(p.communityLabel||'社区'+p.community)+
      '</span>';
      html += '</div>';
      html += '</div>';
    });
    html += '</div>';
  }

  if(data.bridge_papers && data.bridge_papers.length){
    html += '<div class="frontier-section">';
    html += '<div class="frontier-section-title"><span class="frontier-section-icon">🌉</span>跨社区桥梁论文</div>';
    data.bridge_papers.forEach(function(p){
      html += '<div class="frontier-item" onclick="selectPaper(\''+p.id+'\',\''+escHtml(p.name)+'\')">';
      html += '<div class="frontier-item-name">'+escHtml(p.name)+'</div>';
      html += '<div class="frontier-item-meta">';
      html += '<span>📅 '+p.year+'</span>';
      html += '<span class="frontier-badge bridge">跨'+p.cross_communities+'个社区</span>';
      html += '<span style="color:#5c7cfa">PR:'+formatPR(p.pagerank)+'</span>';
      html += '</div>';
      html += '</div>';
    });
    html += '</div>';
  }

  if(!html){
    html = '<div class="default-msg">当前网络暂无前沿论文数据</div>';
  }

  document.getElementById('frontier-content').innerHTML = html;
}

document.addEventListener('DOMContentLoaded',function(){
  initChart();

  var input = document.getElementById('search-input');
  input.addEventListener('input',function(){
    clearTimeout(suggestTimer);
    suggestTimer=setTimeout(function(){fetchSuggestions(input.value);},280);
  });
  document.getElementById('search-btn').addEventListener('click',function(){fetchSuggestions(input.value);});
  input.addEventListener('keypress',function(e){ if(e.key==='Enter') fetchSuggestions(input.value); });
  document.addEventListener('click',function(e){ if(!e.target.closest('.search-area')) hideSuggest(); });

  document.querySelectorAll('.layout-btn').forEach(function(btn){
    btn.addEventListener('click',function(){
      document.querySelectorAll('.layout-btn').forEach(function(b){b.classList.remove('active');});
      btn.classList.add('active');
      currentLayout = btn.dataset.layout;
      if(currentNodes.length>0) renderChart(currentNodes, currentEdges);
    });
  });

  ['nodes-select','hops-select'].forEach(function(id){
    document.getElementById(id).addEventListener('change',function(){
      dataCache.clear();
      if(currentCenterId){
        var n = null;
        for (var i = 0; i < currentNodes.length; i++) {
          if (currentNodes[i].id === currentCenterId) { n = currentNodes[i]; break; }
        }
        selectPaper(currentCenterId, n?n.name:'');
      }
    });
  });

  document.getElementById('center-btn').addEventListener('click',function(){
    if(currentCenterId){
      var n = null;
      for (var i = 0; i < currentNodes.length; i++) {
        if (currentNodes[i].id === currentCenterId) { n = currentNodes[i]; break; }
      }
      dataCache.clear();
      selectPaper(currentCenterId, n?n.name:'');
    } else alert('请先选择一个节点');
  });
  document.getElementById('refresh-btn').addEventListener('click',function(){
    if(currentCenterId){
      var n = null;
      for (var i = 0; i < currentNodes.length; i++) {
        if (currentNodes[i].id === currentCenterId) { n = currentNodes[i]; break; }
      }
      selectPaper(currentCenterId, n?n.name:'');
    }
  });
  document.getElementById('fit-btn').addEventListener('click',function(){
    chart&&chart.dispatchAction({type:'restore'});
  });
  document.getElementById('highlight-upstream-btn').addEventListener('click',function(){highlightChain('upstream');});
  document.getElementById('highlight-downstream-btn').addEventListener('click',function(){highlightChain('downstream');});

  document.getElementById('metrics-toggle').addEventListener('click',function(){
    this.classList.toggle('collapsed');
    var content = document.getElementById('metrics-content');
    content.style.display = content.style.display==='none'?'':'none';
  });
  document.getElementById('frontier-toggle').addEventListener('click',function(){
    this.classList.toggle('collapsed');
    var content = document.getElementById('frontier-content');
    content.style.display = content.style.display==='none'?'':'none';
  });
});
