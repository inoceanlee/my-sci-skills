"use strict";

(function(root){
  const issue=(code,ids,rects,extra={})=>({code,elementIds:ids,rectsPt:rects,...extra});
  const MAX_AUDITED_TEXT_ELEMENTS=128;
  const MAX_TEXT_COLLISION_ISSUES=1024;

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
      const selectAll=selector=>svgs.flatMap(root=>Array.from(root.querySelectorAll(selector)));
      const layoutShapes=node?._fullLayout?.shapes;
      if(Array.isArray(layoutShapes)){
        layoutShapes.forEach((shape,index)=>{
          if(shape?.visible!==false)unknown.push(`layout:shape:${index}`);
        });
      }else if(Array.isArray(node?.layout?.shapes)&&node.layout.shapes.length){
        unknown.push("layout:shapes");
      }

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
      const protectedBoxes=[];
      if(!Array.isArray(protectedAreas)){
        issues.push(issue("PROTECTED_AREA_INVALID",["protected_areas"],[]));
      }else for(const area of protectedAreas){
        const valid=area&&typeof area.id==="string"&&area.id&&
          [area.x_pt,area.y_pt,area.width_pt,area.height_pt].every(Number.isFinite)&&
          area.width_pt>0&&area.height_pt>0;
        const rect=valid?{
          x:area.x_pt/pt,y:area.y_pt/pt,
          w:area.width_pt/pt,h:area.height_pt/pt
        }:null;
        if(!valid||!inCanvas(rect)){
          issues.push(issue("PROTECTED_AREA_INVALID",
            [area?.id||"protected_area"],rect?[rectPt(rect)]:[]));
          continue;
        }
        protectedBoxes.push({id:area.id,rect});
      }
      const visible=element=>{
        let current=element;
        while(current){
          const style=current.ownerDocument.defaultView.getComputedStyle(current);
          if(style.display==="none"||style.visibility==="hidden"||
             style.visibility==="collapse"||Number(style.opacity)===0)return false;
          current=current.parentElement;
        }
        return true;
      };
      const textElements=[];
      let visibleTextCount=0;
      let textLimitReached=false;
      let clippingCount=0;
      let xTickIndex=0,yTickIndex=0;
      const classify=text=>{
        const title=text.closest(".xtitle,.ytitle");
        if(title)return [title.classList.contains("xtitle")?"axis:x_title":"axis:y_title","axis_title"];
        if(text.closest(".xtick"))return ["tick:x:"+xTickIndex++,"tick_label"];
        if(text.closest(".ytick"))return ["tick:y:"+yTickIndex++,"tick_label"];
        if(text.closest(".legend"))return ["legend:text:"+text.textContent.trim(),"legend_text"];
        if(text.closest(".colorbar"))return ["colorbar:text:"+text.textContent.trim(),"colorbar_text"];
        if(text.closest(".annotation"))return ["annotation:"+text.textContent.trim(),"annotation"];
        if(text.closest(".gtitle"))return ["figure:title","figure_title"];
        return ["svg:text:"+text.textContent.trim(),"svg_text"];
      };
      for(const svgRoot of svgs){
        const svgDocument=svgRoot.ownerDocument;
        const nodeFilter=svgDocument.defaultView.NodeFilter;
        const walker=svgDocument.createTreeWalker(svgRoot,nodeFilter.SHOW_ELEMENT,{
          acceptNode:element=>element.localName==="text"
            ?nodeFilter.FILTER_ACCEPT:nodeFilter.FILTER_SKIP
        });
        for(let text=walker.nextNode();text;text=walker.nextNode()){
          if(!visible(text)||!text.textContent.trim())continue;
          visibleTextCount++;
          if(visibleTextCount>MAX_AUDITED_TEXT_ELEMENTS){
            unknown.push("text_elements:limit");
            textLimitReached=true;
            break;
          }
          const [id,role]=classify(text);
          const rect=measure(text);
          if(!rect){unknown.push(id);continue;}
          roles.add(role);
          textElements.push({id,role,rect});
          for(const area of protectedBoxes){
            const overlap=this.intersection(rect,area.rect);
            if(overlap)issues.push(issue("PROTECTED_AREA_CONFLICT",[area.id,id],
              [rectPt(area.rect),rectPt(rect)],{
                overlapPt2:overlap.w*pt*overlap.h*pt
              }));
          }
          if(!inCanvas(rect)){
            clippingCount++;
            issues.push(issue("GEOMETRY_CLIPPING",[id],[rectPt(rect)]));
          }
        }
        if(textLimitReached)break;
      }

      const legendElements=[];
      for(const legend of selectAll(".legend")){
        if(!visible(legend))continue;
        const rect=measure(legend);
        if(!rect){unknown.push("legend:geometry");continue;}
        const id="legend:"+(legendElements.length+1);
        roles.add("legend");
        for(const area of protectedBoxes){
          const overlap=this.intersection(rect,area.rect);
          if(overlap)issues.push(issue("PROTECTED_AREA_CONFLICT",[area.id,id],
            [rectPt(area.rect),rectPt(rect)],{
              overlapPt2:overlap.w*pt*overlap.h*pt
            }));
        }
        legendElements.push({id,rect});
        if(!inCanvas(rect)){
          clippingCount++;
          issues.push(issue("GEOMETRY_CLIPPING",[id],[rectPt(rect)]));
        }
      }
      let colorbarIndex=0;
      const colorbarElements=[];
      for(const colorbar of selectAll(".colorbar")){
        if(!visible(colorbar))continue;
        const rect=measure(colorbar);
        if(!rect){unknown.push("colorbar:geometry");continue;}
        const id=`colorbar:${++colorbarIndex}`;
        roles.add("colorbar");
        colorbarElements.push({id,rect});
        if(!inCanvas(rect)){
          clippingCount++;
          issues.push(issue("GEOMETRY_CLIPPING",[id],[rectPt(rect)]));
        }
        for(const area of protectedBoxes){
          const overlap=this.intersection(rect,area.rect);
          if(overlap)issues.push(issue("PROTECTED_AREA_CONFLICT",[area.id,id],
            [rectPt(area.rect),rectPt(rect)],{
              overlapPt2:overlap.w*pt*overlap.h*pt
            }));
        }
      }
      const gapPx=(a,b)=>{
        const dx=Math.max(0,a.x-(b.x+b.w),b.x-(a.x+a.w));
        const dy=Math.max(0,a.y-(b.y+b.h),b.y-(a.y+a.h));
        return Math.hypot(dx,dy);
      };
      for(const axis of ["x","y"]){
        const title=textElements.find(item=>item.id===`axis:${axis}_title`);
        const ticks=textElements.filter(item=>item.id.startsWith(`tick:${axis}:`));
        if(title&&ticks.length){
          const nearest=ticks.reduce((best,item)=>
            gapPx(title.rect,item.rect)<gapPx(title.rect,best.rect)?item:best);
          const gap=gapPx(title.rect,nearest.rect)*pt;
          if(gap<3-.25)issues.push(issue("CLEARANCE_VIOLATION",
            [title.id,nearest.id],[rectPt(title.rect),rectPt(nearest.rect)],
            {gapDeficitPt:3-gap}));
        }
      }
      for(const container of [...legendElements,...colorbarElements]){
        const neighbors=[
          ...textElements.filter(item=>!["legend_text","colorbar_text"].includes(item.role)),
          ...legendElements.filter(item=>item!==container),
          ...colorbarElements.filter(item=>item!==container)
        ];
        if(neighbors.length){
          const nearest=neighbors.reduce((best,item)=>
            gapPx(container.rect,item.rect)<gapPx(container.rect,best.rect)?item:best);
          const gap=gapPx(container.rect,nearest.rect)*pt;
          if(gap<4-.25)issues.push(issue("CLEARANCE_VIOLATION",
            [container.id,nearest.id],[rectPt(container.rect),rectPt(nearest.rect)],
            {gapDeficitPt:4-gap}));
        }
      }
      const outerElements=[...textElements,...legendElements,...colorbarElements];
      if(outerElements.length){
        const edges=[
          ["left",outerElements.reduce((best,item)=>item.rect.x<best.rect.x?item:best)],
          ["right",outerElements.reduce((best,item)=>item.rect.x+item.rect.w>
            best.rect.x+best.rect.w?item:best)],
          ["top",outerElements.reduce((best,item)=>item.rect.y<best.rect.y?item:best)],
          ["bottom",outerElements.reduce((best,item)=>item.rect.y+item.rect.h>
            best.rect.y+best.rect.h?item:best)]
        ];
        for(const [side,item] of edges){
          const gapPxToCanvas=side==="left"?item.rect.x:
            side==="right"?width-item.rect.x-item.rect.w:
            side==="top"?item.rect.y:height-item.rect.y-item.rect.h;
          const gap=gapPxToCanvas*pt;
          if(gap<6-.25)issues.push(issue("CLEARANCE_VIOLATION",
            [item.id,`canvas:${side}`],[rectPt(item.rect)],{
              gapDeficitPt:6-gap
            }));
        }
      }
      let textCollisionCount=0;
      let textCollisionLimitReached=false;
      if(!textLimitReached){
        textPairs:
        for(let i=0;i<textElements.length;i++){
          for(let j=i+1;j<textElements.length;j++){
            const a=textElements[i],b=textElements[j];
            const overlap=this.intersection(a.rect,b.rect);
            if(!overlap)continue;
            if(textCollisionCount>=MAX_TEXT_COLLISION_ISSUES){
              unknown.push("text_collisions:limit");
              textCollisionLimitReached=true;
              break textPairs;
            }
            issues.push(issue("GEOMETRY_COLLISION",[a.id,b.id],
              [rectPt(a.rect),rectPt(b.rect)],{
                overlapPt2:overlap.w*pt*overlap.h*pt
              }));
            textCollisionCount++;
          }
        }
      }
      if(!textLimitReached&&!textCollisionLimitReached){
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
        let scatterMode=null;
        if(type==="scatter"){
          const resolvedMode=Array.isArray(node._fullData)
            ?node._fullData[index]?.mode:null;
          scatterMode=typeof resolvedMode==="string"?resolvedMode:trace.mode;
          if(typeof scatterMode!=="string"){
            unknown.push(`${id}:mode`);
            return;
          }
          if(scatterMode.includes("lines")){
            shapes.push(...group.querySelectorAll("path.js-line"));
            roles.add("data_line");
          }
          if(scatterMode.includes("markers")){
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
          const lineShape=type==="scatter"&&scatterMode.includes("lines")&&
            shape.matches("path.js-line");
          const pathGeometry=lineShape?this.pathGeometry(shape,width,height):null;
          if(lineShape&&!pathGeometry){unknown.push(`${id}:path_geometry`);return;}
          for(const area of protectedBoxes){
            const overlap=this.intersection(rect,area.rect);
            const hits=lineShape
              ? this.pathHits(shape,area.rect,plotRect,width,height,pathGeometry):Boolean(overlap);
            if(hits===null){unknown.push(`${id}:path_geometry`);return;}
            if(hits)issues.push(issue("PROTECTED_AREA_CONFLICT",[area.id,id],
              [rectPt(area.rect),rectPt(rect)],{
                overlapPt2:overlap?overlap.w*pt*overlap.h*pt:undefined
              }));
          }
          for(const legend of legendElements){
            const overlap=this.intersection(rect,legend.rect);
            if(!overlap)continue;
            const hits=lineShape
              ? this.pathHits(shape,legend.rect,plotRect,width,height,pathGeometry):true;
            if(hits===null){unknown.push(`${id}:path_geometry`);return;}
            if(hits){
              issues.push(issue("DATA_OCCLUSION",[legend.id,id],[rectPt(legend.rect),rectPt(rect)]));
              break;
            }
          }
          if(!textLimitReached&&!textCollisionLimitReached){
            for(const text of textElements){
              if(text.role==="legend_text")continue;
              const textRect=plotRect?this.intersection(text.rect,plotRect):text.rect;
              if(!textRect)continue;
              const overlap=this.intersection(rect,textRect);
              if(!overlap)continue;
              const hits=lineShape
                ?this.pathHits(shape,textRect,plotRect,width,height,pathGeometry)
                :Boolean(overlap);
              if(hits===null){unknown.push(`${id}:path_geometry`);return;}
              if(hits)issues.push(issue("DATA_OCCLUSION",[text.id,id],
                [rectPt(textRect),rectPt(rect)],{
                  overlapPt2:overlap.w*pt*overlap.h*pt
                }));
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

    segmentIntersectsRect(x1,y1,x2,y2,rect){
      const dx=x2-x1,dy=y2-y1;
      let lower=0,upper=1;
      let p=-dx,q=x1-rect.x;
      if(p===0){if(q<0)return false;}
      else{
        const t=q/p;
        if(p<0){if(t>upper)return false;if(t>lower)lower=t;}
        else{if(t<lower)return false;if(t<upper)upper=t;}
      }
      p=dx;q=rect.x+rect.w-x1;
      if(p===0){if(q<0)return false;}
      else{
        const t=q/p;
        if(p<0){if(t>upper)return false;if(t>lower)lower=t;}
        else{if(t<lower)return false;if(t<upper)upper=t;}
      }
      p=-dy;q=y1-rect.y;
      if(p===0){if(q<0)return false;}
      else{
        const t=q/p;
        if(p<0){if(t>upper)return false;if(t>lower)lower=t;}
        else{if(t<lower)lower=t;if(t<upper)upper=t;}
      }
      p=dy;q=rect.y+rect.h-y1;
      if(p===0){if(q<0)return false;}
      else{
        const t=q/p;
        if(p<0){if(t>upper)return false;if(t>lower)lower=t;}
        else{if(t<lower)lower=t;if(t<upper)upper=t;}
      }
      return lower<=upper;
    }

    pathGeometry(path,width,height){
      try{
        const pathData=path.getAttribute("d");
        if(typeof pathData!=="string"||pathData.length===0||pathData.length>1_000_000||
           !Number.isFinite(width)||width<=0||!Number.isFinite(height)||height<=0)return null;
        const tokens=pathData.match(/[A-Za-z]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?/g);
        if(!tokens||tokens.join("")!==pathData.replace(/[\s,]+/g,""))return null;
        const rootRect=path.ownerSVGElement?.getBoundingClientRect();
        const matrix=path.getScreenCTM();
        if(!matrix||!(rootRect?.width>0&&rootRect?.height>0))return null;
        if(![rootRect.left,rootRect.top,rootRect.width,rootRect.height].every(Number.isFinite))return null;
        const style=path.ownerDocument?.defaultView?.getComputedStyle(path);
        if(!style)return null;
        const stroke=style.stroke==="none"?0:Number.parseFloat(style.strokeWidth);
        if(!Number.isFinite(stroke)||stroke<0)return null;
        const scaleX=Math.hypot(matrix.a,matrix.b),scaleY=Math.hypot(matrix.c,matrix.d);
        const shear=matrix.a*matrix.c+matrix.b*matrix.d;
        if(![scaleX,scaleY,shear].every(Number.isFinite))return null;
        const nonScalingStroke=style.vectorEffect==="non-scaling-stroke";
        if(stroke>0&&style.vectorEffect!=="none"&&!nonScalingStroke)return null;
        if(stroke>0&&!nonScalingStroke){
          const tolerance=1e-8*Math.max(1,scaleX*scaleY);
          if(Math.abs(scaleX-scaleY)>tolerance||Math.abs(shear)>tolerance)return null;
        }
        const strokeScale=nonScalingStroke?1:(scaleX+scaleY)/2;
        const geometry={segments:[],strokeX:stroke/2*strokeScale*width/rootRect.width,
          strokeY:stroke/2*strokeScale*height/rootRect.height};
        let index=0,command=null,current=null,start=null;
        const project=(localX,localY)=>{
          const screen=new DOMPoint(localX,localY).matrixTransform(matrix);
          const x=(screen.x-rootRect.left)/rootRect.width*width;
          const y=(screen.y-rootRect.top)/rootRect.height*height;
          if(![localX,localY,screen.x,screen.y,x,y].every(Number.isFinite))return null;
          return {localX,localY,x,y};
        };
        const addSegment=point=>{
          if(!current||geometry.segments.length>=400_000)return false;
          geometry.segments.push(current.x,current.y,point.x,point.y);
          current=point;
          return true;
        };
        while(index<tokens.length){
          if(/^[A-Za-z]$/.test(tokens[index])){
            command=tokens[index++];
            if(!"MmLlHhVvZz".includes(command))return null;
            if(command.toUpperCase()==="Z"){
              if(!current||!start||!addSegment(start))return null;
              current=start;command=null;
              continue;
            }
          }else if(!command)return null;
          const operation=command.toUpperCase();
          const relative=command!==operation;
          let localX,localY;
          if(operation==="M"||operation==="L"){
            if(index+1>=tokens.length||/[A-Za-z]/.test(tokens[index])||/[A-Za-z]/.test(tokens[index+1]))return null;
            localX=Number(tokens[index++]);localY=Number(tokens[index++]);
            if(relative){
              if(!current&&operation!=="M")return null;
              localX+=(current?.localX??0);localY+=(current?.localY??0);
            }
          }else if(operation==="H"){
            if(index>=tokens.length||/[A-Za-z]/.test(tokens[index])||!current)return null;
            localX=Number(tokens[index++]);localY=current.localY;
            if(relative)localX+=current.localX;
          }else{
            if(index>=tokens.length||/[A-Za-z]/.test(tokens[index])||!current)return null;
            localX=current.localX;localY=Number(tokens[index++]);
            if(relative)localY+=current.localY;
          }
          if(![localX,localY].every(Number.isFinite))return null;
          const point=project(localX,localY);
          if(!point)return null;
          if(operation==="M"){
            current=point;start=point;command=relative?"l":"L";
          }else if(!addSegment(point))return null;
        }
        return geometry;
      }catch{return null;}
    }

    pathHits(path,rect,plotRect,width,height,geometry=null){
      geometry=geometry||this.pathGeometry(path,width,height);
      if(!geometry)return null;
      const x=Math.max(rect.x-geometry.strokeX,plotRect?.x??rect.x-geometry.strokeX);
      const y=Math.max(rect.y-geometry.strokeY,plotRect?.y??rect.y-geometry.strokeY);
      const right=Math.min(rect.x+rect.w+geometry.strokeX,
        plotRect?plotRect.x+plotRect.w:rect.x+rect.w+geometry.strokeX);
      const bottom=Math.min(rect.y+rect.h+geometry.strokeY,
        plotRect?plotRect.y+plotRect.h:rect.y+rect.h+geometry.strokeY);
      if(right<x||bottom<y)return false;
      const targetRect={x,y,w:right-x,h:bottom-y};
      for(let index=0;index<geometry.segments.length;index+=4){
        if(this.segmentIntersectsRect(geometry.segments[index],geometry.segments[index+1],
          geometry.segments[index+2],geometry.segments[index+3],targetRect))return true;
      }
      return false;
    }
  }

  if(typeof module!=="undefined"&&module.exports)module.exports={PlotlyGeometryAuditor};
  if(typeof window!=="undefined")root.ScientificFigureAudit={PlotlyGeometryAuditor};
})(typeof window!=="undefined"?window:{});
