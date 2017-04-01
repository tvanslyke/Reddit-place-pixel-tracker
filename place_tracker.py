import websocket
import json
import numpy as np
import struct
import urllib2


def auto_get_url():
    """ Get the url of the r/place websocket that can provide the updates to us. """
    response = urllib2.urlopen(r'https://www.reddit.com/place?webview=true')
    html = response.read()
    findstr = '"place_websocket_url":'
    url = html[html.index(findstr):]
    url = url[url.index('wss'):url.index(',')]
    url = url.strip()
    url = url.strip('"')
    return url


class RedditPlaceTracker(object):
    """ Small class for tracking updates to the canvas being painted on reddit.com/r/place. """

    # tuple of colors that can be written to the canvas
    COLORS = (np.array((255, 255, 255)),
             np.array((228, 228, 228)),
             np.array((136, 136, 136)),
             np.array((34,   34,  34)),
             np.array((255, 167, 209)),
             np.array((229,   0,   0)),
             np.array((229, 149,   0)),
             np.array((160, 106,  66)),
             np.array((229, 217,   0)),
             np.array((148, 224,  68)),
             np.array((  2, 190,   1)),
             np.array((  0, 211, 221)),
             np.array((  0, 131, 199)),
             np.array((  0, 0,   234)),
             np.array((207, 110, 228)),
             np.array((130,   0, 128)))
    def __init__(self, url = None):
        """ Make a RedditPlaceTracker object.

            @param url:  url of the place websocket from which we will obtain the updates.
                         This is determined automatically if not provided.
        """

        if url is None:
            self.url = auto_get_url()
        else:
            self.url = url        
        self.ws = websocket.create_connection(self.url)
        self.updates = []
 
    def get_update(self, save_update = True):
        """ Query the r/place canvas for the most recent pixel update.

            @param save_update:  if save_update is True, the update will be written
                                 to self.updates.
            returns the position and color index of the pixel in the form: ((x, y), color_index)
        """
        update = json.loads(self.ws.recv())['payload']
        if save_update:
            self.updates.append(((update['x'], update['y']), update['color']))
            return self.updates[-1]
        else:
            return ((update['x'], update['y']), update['color'])
    def to_img(self, start = 0, end = None, img = None):
        """ Write a range of collected updates to an image.
            Must have called get_update() with save_update = True for this to be worth a damn.
            
            @param start: the index of the first update to include.
            @param end:   the index of the first update to exclude.
            @param img:   img to write updates to.

            returns a np.ndarray(shape = (1000, 1000, 3), dtype = np.uint8) if img is None,
                    otherwise returns 'img' with updates written to it.
        """
        if img is None:
            img = np.ndarray(shape = (1000, 1000, 3), dtype = np.uint8)
            img[:][:][:] = 255
        for update in (self.updates[start:end] if end is not None else self.updates[start:]):
            img[update[0][0] - 1, update[0][1] - 1] = RedditPlaceTracker.COLORS[update[1]]
        return img

    def __enter__(self):
        """ So that we can use with statements (with RedditPlaceTracker() as my_var_name:...). """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """ So that we can use with statements (with RedditPlaceTracker() as my_var_name:...). """
        self.close()
        
    def close(self):
        self.ws.close()
    def continuous_to_file(self, fname, show_updates = False, save_updates = False):
        """ Write updates continuously to file.
            @param fname:        path and name of file to write updates to.
            @param show_updates: set to True to have updates printed as:
                                    'update: [x][y][color]' (binary format: HHB)
                                 looks like 'update: y\x01Q\x01\x03''
            @param save_updates: set to True to have this tracker save updates to self.updates.
            Updates are written in a binary format as:
                (uint16(x position), uint16(y position), uint8(color index)).
            Note that the positions are written with 1-indexing and that the RGB value
            for the color codes are shown COLORS tuple for this class.
            
        """
        with open(fname, "wt") as f:
            while 1:
                try:
                    if show_updates:
                        while 1:
                            
                            data = self.get_update(save_update = save_updates)
                            compact = struct.pack('HHB', data[0][0], data[0][1], data[1])
                            f.write(compact)
                            print "update: " + repr(compact)
                    else:
                        while 1:
                            data = self.get_update(save_update = save_updates)
                            f.write(struct.pack('HHB', data[0][0], data[0][1], data[1]))
                            
                except websocket.WebSocketConnectionClosedException:
                    # attempt to fix broken connection
                    print "Connection closed.  Attempting to reestablish."
                    self.repair_connection()
    def repair_connection(self):
        self.ws = websocket.create_connection(auto_get_url())
                    

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    
    with RedditPlaceTracker() as place:
        print place.get_update(save_update = False)

    
    
    
