import numpy as np
import shutil

def place(n, k, dir_m, dir_i, new_dir):
    old_name = "{:04d}".format(n+1) + ".png"
    new_name = "{:04d}".format(k+1) + ".png"
    shutil.copy(f"{dir_m}/{old_name}", f"{new_dir}/labelcol/{new_name}")
    shutil.copy(f"{dir_i}/{old_name}", f"{new_dir}/img/{new_name}")
    
if __name__ == "__main__":
    P = np.random.permutation(1000)
    
    old_mask = "./masks_512"
    old_im = "./images_512"
    
    for i,p in enumerate(P[:760]):
        place(p, i, old_mask, old_im, "Train")
        
    for i,p in enumerate(P[760:880]):
        place(p, i, old_mask, old_im, "Validate")
         
    for i,p in enumerate(P[880:]):
        place(p, i, old_mask, old_im, "Test")
    
    
