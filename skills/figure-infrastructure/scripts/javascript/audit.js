"use strict";

(function(root){
  const issue=(code,ids,rects,extra={})=>({code,elementIds:ids,rectsPt:rects,...extra});

  class PlotlyGeometryAuditor{
    audit(node,preset,protectedAreas=[]){
      const issues=[];
      const roles=new Set();
      const unknown=[];
      const svgs=Array.from(node?.querySelectorAll?.("svg.main-svg")||[]);
      const svg=svgs[0]||null;
      const width=Number(preset?.widthPx),height=Number(preset?.heightPx),dpi=Number(preset?.dpi);
      if(!svg||!(width>0&&height>0&&dpi>0)){
        return this.result("not_auditable",[
          issue("GEOMETRY_NOT_AUDITABLE",["svg:missing"],[])
        ],[],null,null);
      }
      if(protectedAreas.length)unknown.push("protected_areas");
      const selectAll=selector=>svgs.flatMap(root=>Array.from(root.querySelectorAll(selector)));

      let viewBox=svg.viewBox?.baseVal;
      if(!viewBox||!(viewBox.width>0&&viewBox.height>0)){
        const values=(svg.getAttribute("viewBox")||"").trim().split(/[ ,]+/).map(Number);
        if(values.length===4&&values.every(Number.isFinite)&&values[2]>0&&values[3]>0){
          viewBox={x:values[0],y:values[1],width:values[2],height:values[3]};
        }else{
          viewBox={x:0,y:0,
            width:svg.width?.baseVal?.value||Number(svg.getAttribute("width"))||width,
            height:svg.height?.baseVal?.value||Number(svg.getAttribute("height"))||height};
        }
      }
      let inverse;
      try{
        if(!viewBox||!(viewBox.width>0&&viewBox.height>0))throw new Error();
        inverse=svg.getScreenCTM()?.inverse();
        if(!inverse)throw new Error();
      }catch{
        return this.result("not_auditable",[
          issue("GEOMETRY_NOT_AUDITABLE",["svg:transform"],[])
        ],[],null,null);
      }
      const scaleX=width/viewBox.width,scaleY=height/viewBox.height;
      const pt=72/dpi;
      const rectPt=rect=>[
        rect.x*72/dpi,
        rect.y*72/dpi,
        rect.w*72/dpi,
        rect.h*72/dpi
      ];
      const measure=(element,expandStroke=false)=>{
        const elementSvg=element.ownerSVGElement||svg;
        const svgRect=elementSvg.getBoundingClientRect();
        const rect=element.getBoundingClientRect();
        if(!(svgRect.width>0&&svgRect.height>0)||
           ![rect.left,rect.top,rect.width,rect.height].every(Number.isFinite))return null;
        const stroke=expandStroke?Math.max(1,Number.parseFloat(
          element.ownerDocument.defaultView.getComputedStyle(element).strokeWidth
        )||1):0;
        const strokeX=stroke/svgRect.width*width,strokeY=stroke/svgRect.height*height;
        return {
          x:(rect.left-svgRect.left)/svgRect.width*width-strokeX/2,
          y:(rect.top-svgRect.top)/svgRect.height*height-strokeY/2,
          w:Math.max(rect.width,stroke)/svgRect.width*width,
          h:Math.max(rect.height,stroke)/svgRect.height*height
        };
      };
      const inCanvas=rect=>rect.x>=0&&rect.y>=0&&rect.x+rect.w<=width&&rect.y+rect.h<=height;
      const visible=element=>{
        const style=element.ownerDocument.defaultView.getComputedStyle(element);
        return style.display!=="none"&&style.visibility!=="hidden"&&Number(style.opacity)!==0;
      };
      const textElements=[];
      let clippingCount=0;
      const classify=text=>{
        const title=text.closest(".xtitle,.ytitle");
        if(title)return [title.classList.contains("xtitle")?"axis:x_title":"axis:y_title","axis_title"];
        if(text.closest(".xtick"))return ["tick:x:"+selectAll(".xtick text").indexOf(text),"tick_label"];
        if(text.closest(".ytick"))return ["tick:y:"+selectAll(".ytick text").indexOf(text),"tick_label"];
        if(text.closest(".legend"))return ["legend:text:"+text.textContent.trim(),"legend_text"];
        if(text.closest(".colorbar"))return ["colorbar:text:"+text.textContent.trim(),"colorbar_text"];
        if(text.closest(".annotation"))return ["annotation:"+text.textContent.trim(),"annotation"];
        if(text.closest(".gtitle"))return ["figure:title","figure_title"];
        return ["svg:text:"+text.textContent.trim(),"svg_text"];
      };
      for(const text of selectAll("text")){
        if(!visible(text)||!text.textContent.trim())continue;
        const [id,role]=classify(text);
        const rect=measure(text);
        if(!rect){unknown.push(id);continue;}
        roles.add(role);
        textElements.push({id,role,rect});
        if(!inCanvas(rect)){
          clippingCount++;
          issues.push(issue("GEOMETRY_CLIPPING",[id],[rectPt(rect)]));
        }
      }

      const legendElements=[];
      for(const legend of selectAll(".legend")){
        if(!visible(legend))continue;
        const rect=measure(legend);
        if(!rect){unknown.push("legend:geometry");continue;}
        const id="legend:"+(legendElements.length+1);
        roles.add("legend");
        legendElements.push({id,rect});
        if(!inCanvas(rect)){
          clippingCount++;
          issues.push(issue("GEOMETRY_CLIPPING",[id],[rectPt(rect)]));
        }
      }
      for(const colorbar of selectAll(".colorbar")){
        if(!visible(colorbar))continue;
        if(!measure(colorbar))unknown.push("colorbar:geometry");
        else roles.add("colorbar");
      }

      for(let i=0;i<textElements.length;i++){
        for(let j=i+1;j<textElements.length;j++){
          const a=textElements[i],b=textElements[j];
          if(a.role==="annotation"&&b.role==="annotation")continue;
          const overlap=this.intersection(a.rect,b.rect);
          if(overlap){
            issues.push(issue("GEOMETRY_COLLISION",[a.id,b.id],
              [rectPt(a.rect),rectPt(b.rect)],{
                overlapPt2:overlap.w*pt*overlap.h*pt
              }));
          }
        }
      }
      for(const legend of legendElements){
        for(const text of textElements){
          if(text.role==="legend_text")continue;
          const overlap=this.intersection(legend.rect,text.rect);
          if(overlap)issues.push(issue("GEOMETRY_COLLISION",[text.id,legend.id],
            [rectPt(text.rect),rectPt(legend.rect)],{
              overlapPt2:overlap.w*pt*overlap.h*pt
            }));
        }
      }

      const plotSize=node._fullLayout?._size;
      const plotRect=plotSize&&[plotSize.l,plotSize.t,plotSize.w,plotSize.h].every(Number.isFinite)
        ? {x:(plotSize.l-viewBox.x)*scaleX,y:(plotSize.t-viewBox.y)*scaleY,
          w:plotSize.w*scaleX,h:plotSize.h*scaleY}:null;
      const data=Array.isArray(node.data)?node.data:[];
      if(!Array.isArray(node.data))unknown.push("trace:data");
      const supported=new Set(["scatter","bar","heatmap","contour"]);
      data.forEach((trace,index)=>{
        const type=trace.type||"scatter";
        const id=`data:${type}:${index}`;
        if(!supported.has(type)){
          unknown.push(id);
          return;
        }
        if(this.hasNonFinite(trace.x)||this.hasNonFinite(trace.y)||
           this.hasNonFinite(trace.z)||this.hasNonFinite(trace.values)){
          unknown.push(id+":non_finite");
          return;
        }
        const selector={
          scatter:".scatterlayer g.trace",
          bar:".barlayer g.trace",
          heatmap:".heatmaplayer .hm",
          contour:".contourlayer g.trace"
        }[type];
        const ordinal=data.slice(0,index).filter(item=>(item.type||"scatter")===type).length;
        const group=selectAll(selector)[ordinal]||null;
        if(!group){
          const values=[trace.x,trace.y,trace.z,trace.values].filter(Array.isArray);
          if(values.some(value=>value.length))unknown.push(id+":svg_geometry");
          return;
        }
        let shapes=[];
        if(type==="scatter"){
          const mode=trace.mode||"lines";
          if(mode.includes("lines")){
            shapes.push(...group.querySelectorAll("path.js-line"));
            roles.add("data_line");
          }
          if(mode.includes("markers")){
            shapes.push(...group.querySelectorAll("path.point,circle.point"));
            roles.add("data_marker");
          }
        }else if(type==="bar"){
          shapes.push(...group.querySelectorAll("path,rect"));
          roles.add("data_bar");
        }else{
          shapes.push(...group.querySelectorAll("image,path,rect"));
          roles.add("data_field");
        }
        if(shapes.length===0){
          const values=[trace.x,trace.y,trace.z,trace.values].filter(Array.isArray);
          if(values.some(value=>value.length))unknown.push(id+":svg_geometry");
        }
        shapes.forEach((shape,shapeIndex)=>{
          const rect=measure(shape,shape.matches("path.js-line"));
          if(!rect){unknown.push(`${id}:element:${shapeIndex}`);return;}
          for(const legend of legendElements){
            const overlap=this.intersection(rect,legend.rect);
            if(!overlap)continue;
            const hits=type==="scatter"&&modeHasLines(trace)
              ? this.pathHits(shape,legend.rect,plotRect,width,height):true;
            if(hits){
              issues.push(issue("DATA_OCCLUSION",[legend.id,id],[rectPt(legend.rect),rectPt(rect)]));
              break;
            }
          }
        });
      });

      const uniqueIssues=[];
      const seen=new Set();
      for(const item of issues){
        const key=item.code+":"+item.elementIds.join("|");
        if(!seen.has(key)){seen.add(key);uniqueIssues.push(item);}
      }
      let collisionCount=uniqueIssues.filter(item=>
        item.code==="GEOMETRY_COLLISION"||item.code==="DATA_OCCLUSION"
      ).length;
      let status;
      if(unknown.length){
        status="not_auditable";
        collisionCount=null;
        for(const id of new Set(unknown))uniqueIssues.push(
          issue("GEOMETRY_NOT_AUDITABLE",[id],[])
        );
      }else status=uniqueIssues.length?"failed":"passed";
      return this.result(status,uniqueIssues,Array.from(roles).sort(),collisionCount,clippingCount);
    }

    result(geometryStatus,geometryIssues,auditedRoles,collisionCount,clippingCount){
      return {geometryStatus,geometryIssues,auditedRoles,collisionCount,clippingCount};
    }

    intersection(a,b){
      const x=Math.max(a.x,b.x),y=Math.max(a.y,b.y);
      const right=Math.min(a.x+a.w,b.x+b.w),bottom=Math.min(a.y+a.h,b.y+b.h);
      return right>x&&bottom>y?{x,y,w:right-x,h:bottom-y}:null;
    }

    hasNonFinite(value){
      if(typeof value==="number")return !Number.isFinite(value);
      if(ArrayBuffer.isView(value)){
        for(const item of value)if(this.hasNonFinite(item))return true;
      }else if(Array.isArray(value)){
        for(const item of value)if(this.hasNonFinite(item))return true;
      }
      return false;
    }

    pathHits(path,rect,plotRect,width,height){
      try{
        const matrix=path.getScreenCTM();
        const total=path.getTotalLength();
        if(!matrix||!Number.isFinite(total))return false;
        const stride=Math.max(1,total/10000);
        for(let offset=0;offset<=total;offset+=stride){
          const local=path.getPointAtLength(Math.min(offset,total));
          const rootRect=path.ownerSVGElement?.getBoundingClientRect();
          if(!(rootRect?.width>0&&rootRect?.height>0))return false;
          const screenPoint=new DOMPoint(local.x,local.y).matrixTransform(matrix);
          const point={
            x:(screenPoint.x-rootRect.left)/rootRect.width*width,
            y:(screenPoint.y-rootRect.top)/rootRect.height*height
          };
          const inPlot=!plotRect||(point.x>=plotRect.x&&point.x<=plotRect.x+plotRect.w&&
            point.y>=plotRect.y&&point.y<=plotRect.y+plotRect.h);
          if(inPlot&&point.x>=rect.x&&point.x<=rect.x+rect.w&&
             point.y>=rect.y&&point.y<=rect.y+rect.h)return true;
        }
      }catch{return false;}
      return false;
    }
  }

  const modeHasLines=trace=>(trace.mode||"lines").includes("lines");
  if(typeof module!=="undefined"&&module.exports)module.exports={PlotlyGeometryAuditor};
  if(typeof window!=="undefined")root.ScientificFigureAudit={PlotlyGeometryAuditor};
})(typeof window!=="undefined"?window:{});
