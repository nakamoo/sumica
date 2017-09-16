class ActivityTest(Controller):
    def __init__(self, user):
        self.user = user
        self.re = []
        self.history = []
        self.msg = ""
        
    def control_hue(self, summary):
        hue = 10000
        bri = 255
        msg = "NONE"
        vec = [0, 0, 0, 0, 0]
        act_id = 0
        alpha = 1

        for obj in summary:
            if obj["label"] == "person":
                act_id = 1

                if "laptop" in obj["touching"]:
                    print("laptop")
                    act_id = 2
                    #alpha = 2
                    break
                elif  "book" in obj["touching"]:
                    print("book")
                    act_id = 3
                    #alpha = 2
                    break
                elif "cell phone" in obj["touching"]:
                    print("phone")
                    act_id = 4
                    #alpha = 2
                    break
                else:
                    print("just person")
                    
        labels = ["no person", "person", "laptop", "book", "phone"]
        vec[act_id] = alpha
    
        self.history.append(vec)
        
        if len(self.history) >= 2:
            data = self.history[-2:]
            
            weights = np.mean(data, axis=0)
            decision = np.argmax(weights)
            print(labels[decision], [label + ": " + str(weight) for label, weight in zip(labels, weights)])

            if decision == 0:
                bri = 100
                hue = 10000
            elif decision == 1:
                bri = 255
            elif decision == 2 or decision == 4:
                bri = 255
                hue = 20000
            elif decision == 3:
                bri = 255
                hue = 50000
        
        self.re =  [{"platform": "hue", "data": json.dumps({"on": True, "hue":hue, "brightness":bri})}]

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"]

            if msg == "activity?":
              n = db.mongo.images.find({"user_name": self.user, "summary":{"$exists": True}}).sort([("time",-1)]).limit(1).next()
              summ = n["summary"]
              
              #touched_obj, looked_obj = extract_features()
              #print(touched_obj, looked_obj)
        elif event == "summary":
            summ = data["summary"]
            extract_features(summ)
            db.mongo.images.update_one({"_id": data["_id"]}, {'$set': {'summary': summ}}, upsert=False)
            
            self.control_hue(summ)