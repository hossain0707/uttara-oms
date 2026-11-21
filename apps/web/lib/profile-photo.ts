/** Resize locally and remove metadata before submitting an authenticated profile save. */
export async function prepareProfilePhoto(file:File):Promise<string>{
 if(!['image/jpeg','image/png','image/webp'].includes(file.type))throw new Error('Choose a JPG, PNG or WebP photo.');
 if(file.size>5*1024*1024)throw new Error('Choose a photo smaller than 5 MB.');
 const bitmap=await createImageBitmap(file);
 try{
  if(bitmap.width<1||bitmap.height<1||bitmap.width*bitmap.height>40000000)throw new Error('Choose a smaller photo.');
  const canvas=document.createElement('canvas');canvas.width=384;canvas.height=384;
  const context=canvas.getContext('2d');if(!context)throw new Error('Photo processing is unavailable in this browser.');
  context.fillStyle='#fff';context.fillRect(0,0,384,384);
  const side=Math.min(bitmap.width,bitmap.height);context.drawImage(bitmap,(bitmap.width-side)/2,(bitmap.height-side)/2,side,side,0,0,384,384);
  const photo=canvas.toDataURL('image/jpeg',.82);if(photo.length>150000)throw new Error('Choose a simpler or smaller photo.');return photo;
 }finally{bitmap.close();}
}
