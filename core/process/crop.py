import os
import nrrd
import numpy as np
from core.utils.filemanip import split_filename


class ImageCropping():
    
    def __init__(self, image, mask=None, prefix=None):
        print('\nStarting image cropping...')

        self.image = image
        self.mask = mask

        imagePath, imageFilename, imageExt = split_filename(image)
        filename = imageFilename.split('.')[0]
        if mask is not None:
            _, maskFilename, maskExt = split_filename(mask)
            self.maskOutname = os.path.join(imagePath, maskFilename+'_cropped')+maskExt

        if prefix is None and mask is not None:
            self.imageOutname = os.path.join(imagePath, filename+'_cropped')+imageExt
        elif prefix is None and mask is None:
            self.imageOutname = os.path.join(imagePath, filename+'_cropped')
        elif prefix is not None and mask is None:
            self.imageOutname = os.path.join(imagePath, prefix+'_cropped')
        elif prefix is not None and mask is not None:
            self.imageOutname = os.path.join(imagePath, prefix+'_cropped')+imageExt

    def crop_with_mask(self, size=[86, 86, 86]):
        
        maskData, maskHD = nrrd.read(self.mask)
        imageData, imageHD = nrrd.read(self.image)
        
        x, y, z = np.where(maskData==1)
        x_size = np.max(x)-np.min(x)
        y_size = np.max(y)-np.min(y)
        z_size = np.max(z)-np.min(z)
        maskMax = np.max(maskData)
        maskMin = np.min(maskData)
        if maskMax > 1 and maskMin < 0:
            print('This image {} is probably not a mask, as it is not binary. '
                  'It will be ignored. Please check if it is true.'.format(self.mask))
            self.imageOutname = None
            self.maskOutname = None
        else:
            if size:
                offset_x = (size[0]-x_size)/2
                offset_y = (size[1]-y_size)/2
                offset_z = (size[2]-z_size)/2
                if offset_x < 0 or offset_y < 0 or offset_z < 0:
                    raise Exception('Size too small, please increase.')
        
                if offset_x.is_integer():
                    new_x = [np.min(x)-offset_x, np.max(x)+offset_x]
                else:
                    new_x = [np.min(x)-(offset_x-0.5), np.max(x)+(offset_x+0.5)]
                if offset_y.is_integer():
                    new_y = [np.min(y)-offset_y, np.max(y)+offset_y]
                else:
                    new_y = [np.min(y)-(offset_y-0.5), np.max(y)+(offset_y+0.5)]
                if offset_z.is_integer():
                    new_z = [np.min(z)-offset_z, np.max(z)+offset_z]
                else:
                    new_z = [np.min(z)-(offset_z-0.5), np.max(z)+(offset_z+0.5)]
                new_x = [int(x) for x in new_x]
                new_y = [int(x) for x in new_y]
                new_z = [int(x) for x in new_z]
            else:
                new_x = [np.min(x)-20, np.max(x)+20]
                new_y = [np.min(y)-20, np.max(y)+20]
                new_z = [np.min(z)-20, np.max(z)+20]
            croppedMask = maskData[new_x[0]:new_x[1], new_y[0]:new_y[1],
                                   new_z[0]:new_z[1]]
            maskHD['sizes'] = np.array(croppedMask.shape)
            
            croppedImage = imageData[new_x[0]:new_x[1], new_y[0]:new_y[1],
                                     new_z[0]:new_z[1]]
            imageHD['sizes'] = np.array(croppedImage.shape)
            
            nrrd.write(self.imageOutname, croppedImage, header=imageHD)
            nrrd.write(self.maskOutname, croppedMask, header=maskHD)
        print('Cropping done!\n')
        return self.imageOutname, self.maskOutname

    def crop_wo_mask(self):

        im, imageHD = nrrd.read(self.image)
        
        _, _, dimZ = im.shape
        
        deltaZ = int(np.ceil((dimZ-86)/2))
        mean_Z = int(np.ceil((dimZ)/2))

        im = im[:, :200, :]
        im[im<-200] = -1024
        x, y= np.where(im[:,:,mean_Z]!=-1024)
        indY = np.max(y)
        uniq = list(set(x))
        xx = [uniq[0]]
        for i in range(1, len(uniq)): 
            if uniq[i]!=uniq[i-1]+1:
                xx.append(uniq[i-1])
                xx.append(uniq[i])
                print(i)
        xx.append(uniq[-1])

        im, _ = nrrd.read(self.image)
        n_mice = 0
        out = []
        for i in range(0, len(xx), 2):
            size = xx[i+1] - xx[i]
            mp = int((xx[i+1] + xx[i])/2)
            if size % 2 != 0:
                size = size+1
            if size > 86:
                deltaX = int((size-86)/2)
            else:
                deltaX = 0
            sizeX=xx[i+1]-deltaX-(xx[i]+deltaX)
            croppedImage = im[mp-43:mp+43, indY-86:indY, deltaZ:dimZ-deltaZ]
            imageHD['sizes'] = np.array(croppedImage.shape)
            
            nrrd.write(self.imageOutname+'_mouse_{}.nrrd'.format(n_mice),
                       croppedImage, header=imageHD)
            out.append(self.imageOutname+'_mouse_{}.nrrd'.format(n_mice))
            n_mice += 1

        print('Cropping done!\n')
        return out
