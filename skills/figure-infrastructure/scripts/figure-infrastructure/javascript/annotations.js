"use strict";

/** Real SVG-measured Plotly peak labels with data-anchored leader arrows. */
(function(root) {
  const intersect = (a,b,pad=0) =>
    a.x < b.x+b.w+pad && b.x < a.x+a.w+pad &&
    a.y < b.y+b.h+pad && b.y < a.y+a.h+pad;

  const segmentIntersects = (r,p,q) => {
    // Liang-Barsky segment/rectangle test in absolute SVG pixel coordinates.
    const dx=q.x-p.x, dy=q.y-p.y;
    let near=0,far=1;
    const edge = [
      [-dx,p.x-r.x],[dx,r.x+r.w-p.x],
      [-dy,p.y-r.y],[dy,r.y+r.h-p.y]
    ];
    for(const [direction,distance] of edge){
      if(direction===0) {if(distance<0)return false;}
      else {
        const t=distance/direction;
        if(direction<0){near=Math.max(near,t);}
        else {far=Math.min(far,t);}
        if(near>far)return false;
      }
    }
    return true;
  };

  class PlotlyAnnotationPlacer {
    constructor(plotly) {
      this.plotly=plotly;
    }

    static sanitize(raw) {
      return String(raw).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
    }

    static measureText(svg,text,font) {
      const measure=document.createElementNS("http://www.w3.org/2000/svg","text");
      measure.setAttribute("font-size",String(font.size));
      measure.setAttribute("font-family",font.family||"Arial, sans-serif");
      measure.textContent=text;
      svg.appendChild(measure);
      const b=measure.getBBox();
      measure.remove();
      return {w:Math.ceil(b.width)+14,h:Math.ceil(b.height)+12};
    }

    static lineSegments(node,origin) {
      const xaxis=node._fullLayout.xaxis,yaxis=node._fullLayout.yaxis;
      const segments=[];
      for(const trace of node.data) {
        if(trace.visible===false||trace.visible==="legendonly")continue;
        const type=trace.type||"scatter";
        if(!["scatter","scattergl"].includes(type))continue;
        if(!trace.x||!trace.y)continue;
        const points=[];
        const n=Math.min(trace.x.length,trace.y.length);
        for(let j=0;j<n;j++){
          const x=Number(trace.x[j]),y=Number(trace.y[j]);
          if(!Number.isFinite(x)||!Number.isFinite(y)){points.push(null);continue;}
          const pt={x:xaxis._offset+xaxis.d2p(x),y:yaxis._offset+yaxis.d2p(y)};
          points.push(pt);
        }
        const lines=(trace.mode||"lines").includes("lines");
        if(lines)for(let j=1;j<points.length;j++)
          if(points[j]&&points[j-1])segments.push([points[j-1],points[j]]);
        for(const point of points)if(point)segments.push([point,point]);
      }
      return segments;
    }

    async place(node,items,{allowExisting=false,names=[],profile="paper"}={}) {
      if(!items || items.length===0)return [];
      if(!Array.isArray(items))throw new Error("ANNOTATION_SPEC_INVALID");
      const external=node.layout.annotations||[];
      if(external.length&&!allowExisting)throw new Error("ANNOTATION_EXISTING_UNSUPPORTED");
      const required=items.filter(x=>x.required!==false);
      if(!required.length)return [];
      for(const spec of required){
        if(typeof spec.text!=="string"||!spec.text.trim()||
           !Number.isFinite(spec.x)||!Number.isFinite(spec.y))
          throw new Error("ANNOTATION_SPEC_INVALID");
      }
      const svg=node.querySelector("svg.main-svg");
      if(!svg||!node._fullLayout?.xaxis||!node._fullLayout?.yaxis)
        throw new Error("ANNOTATION_AXES_UNAVAILABLE");
      const size=node._fullLayout._size,xx=node._fullLayout.xaxis,yy=node._fullLayout.yaxis;
      const frame={x:size.l,y:size.t,w:size.w,h:size.h};
      const fonts=node._fullLayout.font||{size:30};
      const font={
        family:fonts.family||"Arial, sans-serif",
        size:profile==="screen"?Math.max(fonts.size-2,12):Math.max(fonts.size-2,23)
      };
      const segments=this.constructor.lineSegments(node,frame);
      const placed=[];
      const obstacles=[];
      const legend=node.querySelector(".legend");
      const rootRect=svg.getBoundingClientRect();
      if(legend){
        const b=legend.getBoundingClientRect();
        obstacles.push({x:b.left-rootRect.left,y:b.top-rootRect.top,w:b.width,h:b.height});
      }
      for(const element of node.querySelectorAll(".annotation .annotation-text")){
        const b=element.getBoundingClientRect();
        obstacles.push({x:b.left-rootRect.left,y:b.top-rootRect.top,w:b.width,h:b.height});
      }
      for(const spec of required){
        const measurement=this.constructor.measureText(svg,spec.text,font);
        const anchor={x:xx._offset+xx.d2p(spec.x),y:yy._offset+yy.d2p(spec.y)};
        if(!Number.isFinite(anchor.x)||!Number.isFinite(anchor.y))
          throw new Error("ANNOTATION_ANCHOR_INVALID");
        const pad=7,w=measurement.w,h=measurement.h;
        const xlo=frame.x+pad+w/2,xhi=frame.x+frame.w-pad-w/2;
        const ylo=frame.y+pad+h/2,yhi=frame.y+frame.h-pad-h/2;
        if(xhi<xlo||yhi<ylo)throw new Error("ANNOTATION_REQUIRED_UNPLACED");
        const positions=[];
        for(let j=0;j<17;j++)for(let i=0;i<23;i++){
          const cx=xlo+(xhi-xlo)*i/22,cy=ylo+(yhi-ylo)*j/16;
          positions.push({x:cx,y:cy,dist:Math.hypot(cx-anchor.x,cy-anchor.y)});
        }
        positions.sort((a,b)=>a.dist-b.dist);
        let chosen=null;
        for(const candidate of positions){
          if(candidate.dist<26)continue;
          const rect={x:candidate.x-w/2,y:candidate.y-h/2,w,h};
          if(obstacles.some(box=>intersect(rect,box,8)))continue;
          if(segments.some(([a,b])=>segmentIntersects(
            {x:rect.x-5,y:rect.y-5,w:rect.w+10,h:rect.h+10},a,b)))continue;
          chosen={candidate,rect};
          break;
        }
        if(!chosen)throw new Error("ANNOTATION_REQUIRED_UNPLACED: "+spec.text);
        obstacles.push(chosen.rect);
        placed.push({
          x:spec.x,y:spec.y,text:spec.text,arrow:true,
          ax:chosen.candidate.x-anchor.x,ay:chosen.candidate.y-anchor.y,
          box:chosen.rect,name:names[placed.length]
        });
      }

      const existingBoxCount=node.querySelectorAll(".annotation .annotation-text").length;
      await this.plotly.relayout(node,{annotations:[
        ...external,
        ...placed.map(p=>({
          name:p.name,x:p.x,y:p.y,xref:"x",yref:"y",
          text:this.constructor.sanitize(p.text),
          showarrow:true,
          ax:p.ax,ay:p.ay,axref:"pixel",ayref:"pixel",
          arrowhead:2,arrowsize:1,arrowwidth:1,arrowcolor:"#666",
          font:{size:font.size,family:font.family,color:"#111"},
          align:"center",xanchor:"center",yanchor:"middle",
          bgcolor:"rgba(255,255,255,0.97)",borderpad:3
        }))
      ]});

      const boxes=[...node.querySelectorAll(".annotation .annotation-text")];
      if(boxes.length!==existingBoxCount+placed.length)
        throw new Error("ANNOTATION_RENDER_MISSING");
      const newBoxes=boxes.slice(existingBoxCount);
      const bounds=newBoxes.map(el=>{
        const b=el.getBoundingClientRect(),offset=svg.getBoundingClientRect();
        return {x:b.left-offset.left,y:b.top-offset.top,w:b.width,h:b.height};
      });
      const area={x:0,y:0,w:size.l+size.w+size.r,h:size.t+size.h+size.b};
      for(let i=0;i<bounds.length;i++) {
        const b=bounds[i];
        if(b.x<5||b.y<5||b.x+b.w>area.w-5||b.y+b.h>area.h-5)
          throw new Error("ANNOTATION_CLIPPED: "+placed[i].text);
        for(let j=0;j<i;j++)if(intersect(b,bounds[j],2))
          throw new Error("ANNOTATION_OVERLAP");
      }
      return placed.map(({x,y,text,arrow,ax,ay,name})=>({x,y,text,arrow,ax,ay,name}));
    }
  }

  if(typeof module!=="undefined"&&module.exports)module.exports={PlotlyAnnotationPlacer};
  if(typeof window!=="undefined")root.ScientificFigureAnnotations={PlotlyAnnotationPlacer};
})(typeof window!=="undefined"?window:{});
