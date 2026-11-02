.pragma library

// Only the early startup boolean is consumed here. Strings, comments, arrays
// and inline tables are tokenised so a path or multiline string cannot masquerade
// as a setting. The canonical Python settings loader still validates the whole
// document after the first ink frame. Invalid/oversized input skips the overlay.
function arrivalEnabled(source) {
    try {
        const text=String(source || "");if(text.length>65536)return false;
        const tokens=[];let at=0;
        while(at<text.length) {
            const c=text[at];
            if(c==="#") { while(at<text.length && text[at]!=="\n")at++;continue; }
            if(c==="\n") { tokens.push({kind:"newline"});at++;continue; }
            if(/\s/.test(c)) { at++;continue; }
            if("[]=.,{}".indexOf(c)>=0) { tokens.push({kind:c});at++;continue; }
            if(c==='"' || c==="'") {
                const triple=text.slice(at,at+3)===c+c+c, start=at;
                at+=triple?3:1;let value="",closed=false;
                while(at<text.length) {
                    if(text.slice(at,at+(triple?3:1))===(triple?c+c+c:c)) { at+=triple?3:1;closed=true;break; }
                    if(c==='"' && text[at]==="\\") {
                        const escape=text[++at];
                        if(escape==="u" || escape==="U") {
                            const length=escape==="u"?4:8,raw=text.slice(at+1,at+1+length);
                            if(!new RegExp("^[0-9a-fA-F]{"+length+"}$").test(raw))throw Error("escape");
                            value+=String.fromCodePoint(parseInt(raw,16));at+=length+1;
                        } else if(triple && /\s/.test(escape)) { while(at<text.length && /\s/.test(text[at]))at++; }
                        else {
                            const escapes={b:"\b",t:"\t",n:"\n",f:"\f",r:"\r",'"':'"',"\\":"\\"};
                            if(escapes[escape]===undefined)throw Error("escape");
                            value+=escapes[escape];at++;
                        }
                    } else { if(!triple && text[at]==="\n")throw Error("string");value+=text[at++]; }
                }
                if(!closed || at<=start)throw Error("string");
                tokens.push({kind:"string",value:value});continue;
            }
            const start=at;while(at<text.length && !/[\s#\[\]=.,{}"']/.test(text[at]))at++;
            if(at===start)throw Error("token");tokens.push({kind:"bare",value:text.slice(start,at)});
        }
        let pos=0,section=[],out={};
        function peek(kind) { return pos<tokens.length && tokens[pos].kind===kind; }
        function take(kind) { if(!peek(kind))throw Error("syntax");return tokens[pos++]; }
        function lines() { while(peek("newline"))pos++; }
        function key() {
            const parts=[];
            do {
                if(parts.length)take(".");
                if(!peek("bare") && !peek("string"))throw Error("key");
                parts.push(tokens[pos++].value);
            } while(peek("."));
            return parts;
        }
        function put(path,value) {
            const name=path.join(".");if(Object.prototype.hasOwnProperty.call(out,name))throw Error("duplicate");out[name]=value;
        }
        function value(path,depth) {
            if(depth>16)throw Error("depth");
            if(peek("{")) {
                pos++;lines();
                while(!peek("}")) {
                    const child=key();take("=");value(path.concat(child),depth+1);lines();
                    if(!peek(","))break;pos++;lines();
                }
                take("}");return;
            }
            if(peek("[")) {
                pos++;lines();
                // Arrays contain no startup booleans; parse their balanced
                // values into temporary paths, without exposing nested keys.
                let index=0;
                while(!peek("]")) {
                    value(path.concat(["["+(index++)+"]"]),depth+1);lines();
                    if(!peek(","))break;pos++;lines();
                }
                take("]");put(path,[]);return;
            }
            if(peek("string")) { put(path,tokens[pos++].value);return; }
            const scalar=take("bare").value;
            // The remaining documented settings need strings, booleans and
            // arrays only. Decimal numbers can appear as schema_version.
            if(peek(".")) { pos++;take("bare");put(path,null);return; }
            put(path,scalar==="false"?false:scalar==="true"?true:null);
        }
        while(pos<tokens.length) {
            lines();if(pos===tokens.length)break;
            if(peek("[")) { pos++;section=key();take("]"); }
            else { const path=section.concat(key());take("=");value(path,0); }
            if(pos<tokens.length && !peek("newline"))throw Error("line");
        }
        const enabled=out["session.arrival"];
        return enabled===undefined || enabled===true;
    } catch(_) { return false; }
}
