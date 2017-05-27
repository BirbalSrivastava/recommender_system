# @AUTHOR: Birbal Srivastava
# @DATE: 12th March 2016
# Project Recommendation Engine (Item-Item, User-User)
import gzip
from math import sqrt

class RecommendationEngine:
    def parse(self,path):
        g = gzip.open(path, 'rb')
        for l in g:
            yield eval(l)

    def normalizeRatings(self,nestedDictionary):
        for key in nestedDictionary:
            sum=0
            for items in nestedDictionary[key]:
               sum = sum+(nestedDictionary[key][items])
            avg= sum/len(nestedDictionary[key])
            for items in nestedDictionary[key]:
                nestedDictionary[key][items]= nestedDictionary[key][items] - avg

    def createDictionary(self,pathOfZipFile):
        dict={}
        for review in self.parse(pathOfZipFile):
            key= self.getKeyFrom(review)
            if review.get(key) not in dict:
                # print "review['reviewerName']: ",review.get(key)
                dict[review.get(key)]={}
                dict[review.get(key)][review['asin']]=review['overall']
            else:
                dict[review.get(key)][review['asin']]=review['overall']
        return dict

    def getKeyFrom(self, dict):
        if dict.get('reviewerName','reviewerID') == 'reviewerID':
            return 'reviewerID'
        else:
            return 'reviewerName'
        # return dict.get('reviewerName','reviewerID')

    def getCosineSimilarityOfPairOfUsers(self, userItemRatingMatrix, user1, user2):
        mutuallyRatedItems = {}
        for item in userItemRatingMatrix[user1]:
            if item in userItemRatingMatrix[user2]: mutuallyRatedItems[item] = 1
        n = len(mutuallyRatedItems)
        if n == 0: return 0
        sumOfSquaredRatingsOfUser1 = sum([(userItemRatingMatrix[user1][items] ** 2) for items in userItemRatingMatrix[user1]])
        sumOfSquaredRatingsOfUser2 = sum([(userItemRatingMatrix[user2][items] ** 2) for items in userItemRatingMatrix[user2]])
        pSum = sum([userItemRatingMatrix[user1][items] * userItemRatingMatrix[user2][items] for items in mutuallyRatedItems])
        denominator = sqrt(sumOfSquaredRatingsOfUser1  * sumOfSquaredRatingsOfUser2)
        if denominator == 0: return 0
        cosineSimilarity = pSum / denominator
        return cosineSimilarity

    def generateRankedMatches(self, data, person, n=4, matchNOtherUsers=getCosineSimilarityOfPairOfUsers):
        rating=[(matchNOtherUsers(self, data, person, other), other) for other in data if other != person]
        rating.sort()
        rating.reverse()
        return rating[0:n]

    def transmuteDictionaryForItemItemMatrix(self,data):
        result={}
        for person in data:
            for item in data[person]:
                result.setdefault(item,{})
                result[item][person]=data[person][item]
        return result

    def calculateAndGetRecommendationsBasedOnWeightedAverage(self, data, loggedInUser, matchLoggedInUserWithOthers=getCosineSimilarityOfPairOfUsers, n=10):
        totals={}
        sumOfSimilarities={}
        for otherUsers in data:
            if otherUsers==loggedInUser: continue
            similarityMetric=matchLoggedInUserWithOthers(self, data, loggedInUser, otherUsers)
            if similarityMetric<=0: continue
            # print " Person: " + loggedInUser + " Other: " + otherUsers + " Similarity: ",similarityMetric
            for item in data[otherUsers]:
                if item not in data[loggedInUser] or data[loggedInUser][item]==0:
                    if data[otherUsers][item] >=0:
                        # print ">> ",item," rating: ",data[otherUsers][item]
                        totals.setdefault(item,0)
                        totals[item]+= data[otherUsers][item] * similarityMetric
                        # Sum of similarities
                        sumOfSimilarities.setdefault(item,0)
                        sumOfSimilarities[item]+=similarityMetric
        # Create the normalized list
        rankings=[(total/sumOfSimilarities[item],item) for item,total in totals.items( )]
        rankings.sort( )
        rankings.reverse( )
        return rankings[0:n]


    def writeDict(self, dict, filename):
         with open(filename, "a") as f:
            f.writelines('{}:{}'.format(k,v) for k, v in dict.items())
            f.write('\n')

    def findName(self,path,asin):
        for review in self.parse(path):
           if (review['asin'] == asin):
               return review['title']

# Yash: Considering "asin": "0615447279", "reviewerName": "Antoinette" as a sample for our testing
def main():
    recomEngine = RecommendationEngine()
    ## Below are going to be the parameters of the program.
    sampleUser="Antoinette"
    sampleItem="0615447279"
    pathOfZipFile="reviews_Baby.json.gz"
    metaDataPath = "meta_Baby.json.gz"
    dict=recomEngine.createDictionary(pathOfZipFile)
    print ("Number of users in the Json: ",len(dict.keys()))
    ##Subtract the mean and normalize
    recomEngine.normalizeRatings(dict)

    ## User-User Collaborative filtering
    ## Find 5 similar users
    print ("Top 5 Similar Users: ",recomEngine.generateRankedMatches(dict,sampleUser,n=5))

    ##Get top 20 preferred items as the recommendation
    listOfItems= recomEngine.calculateAndGetRecommendationsBasedOnWeightedAverage(dict,sampleUser,n=20)
    print ("Top 20 Recommended Items are as per below: \n ",'-'*50)
    ## Using METADATA as well.So Prof no complains now..
    for item in listOfItems:
        print ("\n ",recomEngine.findName(metaDataPath,item[1]))

    ## Item-Item Collaborative filtering
    transformedDict = recomEngine.transmuteDictionaryForItemItemMatrix(dict)
    ## For a given sample Item we need to identify similar items
    ## Get top 10 similar items as the item in question
    similarItems = recomEngine.generateRankedMatches(transformedDict,sampleItem,n=10)
    print("Items similar to ",sampleItem," are as under \n", "-"*50)
    for sim in similarItems:
        print ("\n", recomEngine.findName(metaDataPath,sim[1]))

if __name__ == '__main__':
    main()